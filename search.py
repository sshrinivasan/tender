from datetime import datetime, timezone
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from vector import initialize_vector_store, get_retriever

DB_LOCATION = "./chroma_langchain_db"

embeddings = OllamaEmbeddings(model="mxbai-embed-large")
model = OllamaLLM(model="llama3.2", options={"num_ctx": 8192})

summary_prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant summarizing Canadian government tender search results.
The user searched for: {user_query}

Based on these tenders, write a 2-3 sentence summary of what was found.
Mention the number of results, the types of work involved, and any notable departments or closing dates.
Only use the information provided — do not use training data.

Tenders:
{tenders}
""")
summary_chain = summary_prompt | model


def _extract_tender(doc) -> dict:
    m = doc.metadata
    source = m.get("source", "")

    if source == "merx":
        org = m.get("buyer", "")
        url = m.get("page_url", "")
    elif source == "procuredata":
        org = m.get("organization", "")
        url = m.get("url", "")
    else:
        org = m.get("organization", "")
        urls = m.get("urls", "")
        url = urls.split(",")[0].strip() if urls else ""

    return {
        "title": m.get("title", ""),
        "source": source,
        "organization": org,
        "closing_date": m.get("closing_date", ""),
        "closing_date_ts": m.get("closing_date_ts", 0),
        "region": m.get("region", ""),
        "url": url,
    }


def run_search(query: str, source: str = "both", closing_days: int | None = None, regions: list[str] | None = None) -> dict:
    source_filter = ["merx", "canadabuys", "procuredata"] if source == "all" else [source]

    vector_store = initialize_vector_store("all_tenders", embeddings, DB_LOCATION)
    retriever = get_retriever(vector_store, source_filter=source_filter, closing_days=closing_days, regions=regions or None)

    docs = retriever.invoke(query)
    if not docs:
        return {"summary": "No relevant tenders found.", "tenders": []}

    tenders = [_extract_tender(doc) for doc in docs]

    # Deduplicate by title (chunks of the same tender appear as separate docs)
    seen = set()
    unique_tenders = []
    for t in tenders:
        if t["title"] not in seen:
            seen.add(t["title"])
            unique_tenders.append(t)

    summary = summary_chain.invoke({"user_query": query, "tenders": unique_tenders})

    return {"summary": summary.strip(), "tenders": unique_tenders}
