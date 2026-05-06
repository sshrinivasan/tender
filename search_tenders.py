import argparse
import os
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from vector import initialize_vector_store, get_retriever

DB_LOCATION = "./chroma_langchain_db"

model = OllamaLLM(model="llama3.2", options={"num_ctx": 8192})
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

template = """
You are a helpful assistant that finds relevant tenders based on the users query, and summarizes them for the user in a readable way.
Here is the user query that you will be searching for:{user_query}
Here are the tenders that you can search through. Only use these tenders, do not use any training data that you have in your memory: {new_tenders}

In every case, format your output as in the following examples (Note the first row in each example is the Document itself)

Example 1:
   - Tender Title: Generator Maintenance
   - Relevant links: https://merx.com/tenders/12345, https://merx.com/tenders/12346
   - Issuing Organization: Department of Industry (ISED)
   - Closing Date: May 4, 2026
   - Brief Description: The department is seeking contractors for the maintenance of emergency generators.

Example 2:
   - Tender Title: PR23207 39903-261031 Agricultural tractor
   - Tender links: https://merx.com/tenders/12343
   - Issuing Organization: Department of Public Works and Government Services (PSPC)
   - Closing Date: May 6, 2026
   - Brief Description: The procurement of an agricultural tractor is being issued.

"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


def main():
    parser = argparse.ArgumentParser(description="Search Canadian government tenders using natural language.")
    parser.add_argument("query", help="What kind of tenders to search for")
    parser.add_argument("--date", type=int, choices=[7, 30], metavar="{7,30}",
                        help="Only return tenders closing within this many days")
    parser.add_argument("--source", choices=["merx", "canadabuys", "procuredata", "all"], default="all",
                        help="Which source(s) to search (default: all)")
    args = parser.parse_args()

    if not os.path.exists(DB_LOCATION):
        print(f"Error: Vector database not found at {DB_LOCATION}")
        print("Please run build_vector_db.py first.")
        return

    source_filter = ["merx", "canadabuys", "procuredata"] if args.source == "all" else [args.source]

    vector_store = initialize_vector_store("all_tenders", embeddings, DB_LOCATION)
    retriever = get_retriever(vector_store, 
                              source_filter=source_filter, 
                              closing_days=args.date)

    retrieved_tenders = retriever.invoke(args.query)
    if not retrieved_tenders:
        print("No relevant tenders found.")
        return

    result = chain.invoke({"user_query": args.query, "new_tenders": retrieved_tenders})
    print(result)


if __name__ == "__main__":
    main()
