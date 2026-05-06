import os
import time
import requests
from dotenv import load_dotenv
load_dotenv()
from langchain_core.documents import Document
from utils.date_utils import parse_closing_date_ts
from utils.region_utils import normalize_canadabuys_region

RAPIDAPI_HOST = "procuredata-canadian-government-procurement-api.p.rapidapi.com"
BASE_URL = f"https://{RAPIDAPI_HOST}/tender"
PAGE_SIZE = 100


def _get_api_key() -> str:
    key = os.environ.get("RAPIDAPI_KEY", "")
    if not key:
        raise RuntimeError("RAPIDAPI_KEY environment variable not set")
    return key


def _fetch_all_open_tenders() -> list[dict]:
    """Paginate through all open tenders from the ProcureData API."""
    headers = {
        "x-rapidapi-key": _get_api_key(),
        "x-rapidapi-host": RAPIDAPI_HOST,
    }
    tenders = []
    cursor = None
    page = 0

    while True:
        params = {
            "limit": PAGE_SIZE,
            "status": "open",
            "sort_order": "desc",
        }
        if cursor:
            params["cursor"] = cursor

        # Retry up to 3 times on 5xx errors
        for attempt in range(3):
            resp = requests.get(BASE_URL, headers=headers, params=params, timeout=60)
            if resp.status_code < 500:
                break
            wait = 5 * (attempt + 1)
            print(f"[procuredata] HTTP {resp.status_code} on page {page+1}, retrying in {wait}s...")
            time.sleep(wait)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("results", [])
        tenders.extend(batch)
        page += 1
        print(f"[procuredata] page {page}: fetched {len(batch)} tenders (total so far: {len(tenders)})")

        cursor = data.get("next_cursor")
        if not cursor or not batch:
            break

    return tenders


def _pick_region(raw: str | None) -> str:
    """Pick the first canonical region from a possibly multi-line region string."""
    if not raw:
        return "Unknown"
    for part in raw.split("\n"):
        part = part.strip()
        if not part:
            continue
        canonical = normalize_canadabuys_region(part)
        if canonical != "Unknown":
            return canonical
    # Fall back to normalizing the whole string
    return normalize_canadabuys_region(raw.strip())


def _make_url(tender: dict) -> str:
    url = tender.get("notice_url_en") or tender.get("notice_url_fr") or ""
    if url:
        return url
    ref = tender.get("reference_number", "")
    if ref:
        return f"https://canadabuys.canada.ca/en/tender-opportunities/tender-notice/{ref}"
    return ""


def build_procuredata_documents() -> list[Document]:
    """Fetch all open tenders from ProcureData API and return Document instances."""
    tenders = _fetch_all_open_tenders()
    documents = []

    for i, t in enumerate(tenders):
        title = t.get("title_en") or t.get("title_fr") or ""
        raw_desc = t.get("description_en") or t.get("description_fr") or ""
        searchable_text = " ".join(raw_desc.replace("\r", " ").replace("\n", " ").split())

        closing_date_str = t.get("closing_date") or ""
        raw_region = t.get("regions_of_delivery_en") or t.get("regions_of_delivery_fr") or ""

        base_metadata = {
            "title": title,
            "organization": t.get("department_en") or t.get("department_fr") or "",
            "closing_date": closing_date_str,
            "closing_date_ts": parse_closing_date_ts(closing_date_str),
            "region": raw_region,
            "region_canonical": _pick_region(raw_region),
            "url": _make_url(t),
            "source": "procuredata",
            "source_id": t.get("record_id", str(i)),
            "government_level": t.get("government_level", "federal"),
        }

        max_chars = 1000
        chunks = [searchable_text[j:j+max_chars] for j in range(0, len(searchable_text), max_chars)] if searchable_text else [""]

        for chunk_idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue
            doc_id = f"pd-{t.get('record_id', i)}-{chunk_idx}"
            documents.append(Document(
                page_content=chunk,
                metadata={**base_metadata, "chunk_index": chunk_idx},
                id=doc_id
            ))

        if (i + 1) % 100 == 0:
            print(f"[procuredata] processed {i + 1}/{len(tenders)} tenders into {len(documents)} chunks")

    print(f"[procuredata] done: {len(tenders)} tenders → {len(documents)} document chunks")
    return documents
