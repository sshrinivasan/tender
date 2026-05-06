import io
import json
import os
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

model = OllamaLLM(model="llama3.2", options={"num_ctx": 8192})

detail_prompt = ChatPromptTemplate.from_template("""
You are summarizing a single Canadian government tender page for a procurement professional.

Tender title: {title}
Source: {source}

Page content:
{content}

Write a concise 3-5 sentence summary covering:
- What work or goods are being procured
- Key requirements or qualifications mentioned
- Any notable conditions (mandatory site visit, security clearance, bonding, etc.)
- Any important dates beyond the closing date

Only use information from the page content above. If the content is insufficient, say so briefly.
""")

detail_chain = detail_prompt | model

MERX_AUTH_STATE = os.path.join(os.path.dirname(__file__), "utils", "merx_auth.json")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _load_merx_cookies() -> dict:
    if not os.path.exists(MERX_AUTH_STATE):
        return {}
    with open(MERX_AUTH_STATE) as f:
        state = json.load(f)
    return {
        c["name"]: c["value"]
        for c in state.get("cookies", [])
        if "merx.com" in c.get("domain", "")
    }


def _fetch(url: str, source: str) -> requests.Response:
    session = requests.Session()
    session.headers.update(_HEADERS)
    if source == "merx":
        session.cookies.update(_load_merx_cookies())
    resp = session.get(url, timeout=15)
    resp.raise_for_status()
    return resp


def _extract_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)[:6000]


def _extract_html(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["nav", "footer", "script", "style", "header"]):
        tag.decompose()
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="main-content")
        or soup.find(class_="main-content")
        or soup.body
        or soup
    )
    lines = [l for l in main.get_text(separator="\n", strip=True).splitlines() if l.strip()]
    return "\n".join(lines)[:6000]


def fetch_and_summarize(url: str, source: str, title: str) -> str:
    resp = _fetch(url, source)
    content_type = resp.headers.get("content-type", "")
    is_pdf = "pdf" in content_type or url.lower().split("?")[0].endswith(".pdf")

    content = _extract_pdf(resp.content) if is_pdf else _extract_html(resp.content)
    if not content.strip():
        return "Could not extract content from the tender page."
    result = detail_chain.invoke({"title": title, "source": source, "content": content})
    return result.strip()
