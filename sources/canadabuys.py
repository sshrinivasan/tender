import requests
import io
import pandas as pd
import os
from langchain_core.documents import Document
from utils.date_utils import parse_closing_date_ts



def build_canadabuys_documents():
    """Convert the Canadabuys tender DataFrame into a list of Document instances for vector ingestion.
    Each tender's description is normalized and chunked if it exceeds a certain length, with metadata extracted for each document.
    """
    # Open tender notices (Canadabuys)
    meta = requests.get(
        "https://open.canada.ca/data/api/3/action/resource_show",
        params={"id": "5870de7c-86fe-4d05-8d73-cd412e12fdeb"}
    ).json()

    download_url = meta["result"]["url"]

    # Step 2: Download the file (site blocks default python-requests UA)
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(download_url, headers=headers)

    # Convert the content to a pandas DataFrame
    df = pd.read_csv(io.BytesIO(response.content), encoding='utf-8-sig')
    df = df.fillna("")

    # Build document chunks for vector ingestion if needed
    documents = []

    for i, row in df.iterrows():
        print("{0}: Processing tender: {1}".format(i, row["title-titre-eng"]))
        # Normalize text (remove newlines and collapse whitespace)
        raw = row["tenderDescription-descriptionAppelOffres-eng"]
        searchable_text = raw.replace("\r", " ").replace("\n", " ").strip()
        searchable_text = " ".join(searchable_text.split())

        # Chunk long documents to avoid exceeding embedding model context length
        max_chars = 1000
        chunks = [searchable_text[i:i+max_chars] for i in range(0, len(searchable_text), max_chars)] if searchable_text else [""]

        for chunk_idx, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if not chunk:
                continue
            doc_id = f"{i}-{chunk_idx}"
            document = Document(
                page_content=chunk,
                metadata={
                    "title": row["title-titre-eng"],
                    "urls": row["attachment-piecesJointes-eng"] + "," + row["noticeURL-URLavis-eng"],
                    "organization": row["contractingEntityName-nomEntitContractante-eng"],
                    "closing_date": row["tenderClosingDate-appelOffresDateCloture"],
                    "closing_date_ts": parse_closing_date_ts(str(row["tenderClosingDate-appelOffresDateCloture"])),
                    "region": row["regionsOfOpportunity-regionAppelOffres-eng"],
                    "source_id": str(i),
                    "chunk_index": chunk_idx,
                    "source": "canadabuys"
                },
                id=doc_id
            )
            documents.append(document)
    return documents