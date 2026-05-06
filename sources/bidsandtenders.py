import time
import requests
from langchain_core.documents import Document
from utils.date_utils import parse_closing_date_ts
from utils.region_utils import normalize_bidsandtenders_region

API_URL = "https://bidsandtenders.ic9.esolg.ca/Modules/BidsAndTenders/services/bidsSearch.ashx"
PAGE_SIZE = 200
CRAWL_DELAY = 10  # seconds between page requests per robots.txt

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _fetch_all_open_tenders() -> list[dict]:
    tenders = []
    page = 1

    while True:
        params = {"pageNum": page, "pageSize": PAGE_SIZE, "statusId": 1}
        resp = requests.get(API_URL, params=params, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            print(f"[bidsandtenders] API returned success=false on page {page}")
            break

        page_data = data.get("data", {})
        batch = page_data.get("tenders", [])
        if total is None:
            total = page_data.get("totalCount", 0)
        tenders.extend(batch)
        print(f"[bidsandtenders] page {page}: fetched {len(batch)} tenders (total so far: {len(tenders)} / {total})")

        if not batch or len(tenders) >= total:
            break

        page += 1
        time.sleep(CRAWL_DELAY)

    return tenders


def _extract_uuid(view_url: str) -> str:
    """Extract the UUID from the viewUrl path as a stable source_id."""
    return view_url.rstrip("/").split("/")[-1] if view_url else ""


def build_bidsandtenders_documents() -> list[Document]:
    tenders = _fetch_all_open_tenders()
    documents = []

    for i, t in enumerate(tenders):
        title = t.get("name", "")
        org = t.get("organization", {}).get("displayName", "")
        closing_date_str = t.get("convertedClosingDate", "")
        # utcClosingDate is ISO 8601 UTC — parse directly
        closing_date_ts = parse_closing_date_ts(t.get("utcClosingDate", ""))
        url = t.get("viewUrl", "")
        source_id = _extract_uuid(url)

        region_canonical = normalize_bidsandtenders_region(org, title)

        searchable_text = " ".join(f"{title}\n{org}".replace("\n", " ").split())

        max_chars = 1000
        chunks = [searchable_text[j:j + max_chars] for j in range(0, len(searchable_text), max_chars)] if searchable_text else [""]

        for chunk_idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue
            doc_id = f"bt-{source_id or i}-{chunk_idx}"
            documents.append(Document(
                page_content=chunk,
                metadata={
                    "title": title,
                    "organization": org,
                    "closing_date": closing_date_str,
                    "closing_date_ts": closing_date_ts,
                    "region": org,
                    "region_canonical": region_canonical,
                    "url": url,
                    "source": "bidsandtenders",
                    "source_id": source_id,
                    "chunk_index": chunk_idx,
                },
                id=doc_id,
            ))

        if (i + 1) % 200 == 0:
            print(f"[bidsandtenders] processed {i + 1}/{len(tenders)} tenders into {len(documents)} chunks")

    print(f"[bidsandtenders] done: {len(tenders)} tenders → {len(documents)} document chunks")
    return documents
