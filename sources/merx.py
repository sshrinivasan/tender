import json
import os
from langchain_core.documents import Document
from utils.date_utils import parse_closing_date_ts


def build_merx_documents():
    """Convert the Merx tender JSON data into a list of Document instances for vector ingestion.
    Each tender's title and short_description are concatenated and chunked if it exceeds a certain length,
    with metadata extracted for each document.
    """
    # Load the Merx data from JSON file
    json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'merx', 'all_results.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        merx_data = json.load(f)

    # Build document chunks for vector ingestion
    documents = []

    for i, tender in enumerate(merx_data):
        # Concatenate title and short_description
        title = tender.get('title', '')
        short_desc = tender.get('short_description', '')

        print(f"{i}: Processing tender: {title}")
        
        # Combine title and description with a separator
        combined_text = f"{title}\n\n{short_desc}" if short_desc else title

        # Normalize text (remove excessive newlines and collapse whitespace)
        searchable_text = combined_text.replace("\r", " ").replace("\n", " ").strip()
        searchable_text = " ".join(searchable_text.split())

        # Chunk long documents to avoid exceeding embedding model context length
        max_chars = 1000
        chunks = [searchable_text[i:i+max_chars] for i in range(0, len(searchable_text), max_chars)] if searchable_text else [""]

        for chunk_idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue

            doc_id = f"merx-{i}-{chunk_idx}"
            document = Document(
                page_content=chunk,
                metadata={
                    "title": title,
                    "buyer": tender.get('buyer', ''),
                    "closing_date": tender.get('closing_date', ''),
                    "closing_date_ts": parse_closing_date_ts(tender.get('closing_date', '')),
                    "region": tender.get('region', ''),
                    "published_date": tender.get('published_date', ''),
                    "solicitation_id": tender.get('solicitation_id', ''),
                    "page_url": tender.get('page_url', ''),
                    "mandatory_pre_bid": tender.get('mandatory_pre_bid', False),
                    "source": "merx",
                    "source_id": str(i),
                    "chunk_index": chunk_idx
                },
                id=doc_id
            )
            documents.append(document)

    return documents
