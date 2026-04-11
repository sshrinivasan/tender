import os
from langchain_chroma import Chroma
from langchain_core.documents import Document


def initialize_vector_store(collection_name, embeddings, persist_directory):
    vector_store = Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embeddings
    )
    return vector_store

def populate_vector_db(vector_store, documents):
    """Populate the Chromadb vector store with documents.
    documents: list of Document instances (with .id)
    Uses the module-level vector_store and will batch and re-chunk on failures.
    """

    ids = [getattr(d, 'id', None) or str(i) for i, d in enumerate(documents)]
    try:
        vector_store.add_documents(documents=documents, ids=ids)
    except Exception as e:
        print(f"[warning] add_documents failed: {e}. Attempting batched upload...")
        batch_size = 50
        for start in range(0, len(documents), batch_size):
            end = start + batch_size
            batch_docs = documents[start:end]
            batch_ids = ids[start:end]
            try:
                vector_store.add_documents(documents=batch_docs, ids=batch_ids)
            except Exception as be:
                print(f"[warning] batch upload failed for docs {start}-{end}: {be}. Trying per-document fallback...")
                for doc, did in zip(batch_docs, batch_ids):
                    try:
                        vector_store.add_documents(documents=[doc], ids=[did])
                    except Exception as de:
                        # Try re-chunking the problematic document into smaller pieces and add them
                        content = getattr(doc, 'page_content', '') or ''
                        if not content:
                            print(f"[error] Skipping empty doc {did}")
                            continue
                        small_max = 500
                        small_chunks = [content[i:i+small_max] for i in range(0, len(content), small_max)]
                        small_docs = []
                        small_ids = []
                        for si, sc in enumerate(small_chunks):
                            sid = f"{did}-r{si}"
                            small_docs.append(Document(page_content=sc, metadata={**(getattr(doc, 'metadata', {}) or {}), "rechunked": True}, id=sid))
                            small_ids.append(sid)
                        try:
                            vector_store.add_documents(documents=small_docs, ids=small_ids)
                            print(f"[info] Re-chunked and added doc {did} as {len(small_docs)} pieces")
                        except Exception as final_e:
                            print(f"[error] Failed to add re-chunked pieces for {did}: {final_e}. Skipping.")


def get_retriever(vector_store, source_filter=None):
    """
    Create a retriever from the vector store to retrieve search data.

    Args:
        vector_store: The Chroma vector store instance
        source_filter: Optional list of source names to filter by (e.g., ['canadabuys', 'merx'])

    Returns:
        A retriever configured with k=5 and optional source filtering
    """
    search_kwargs = {"k": 5}

    # Add metadata filter if source_filter is provided
    if source_filter:
        # Chroma filter format: {"source": {"$in": ["canadabuys", "merx"]}}
        search_kwargs["filter"] = {"source": {"$in": source_filter}}

    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    return retriever