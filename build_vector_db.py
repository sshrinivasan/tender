from vector import initialize_vector_store, populate_vector_db
from sources.canadabuys import build_canadabuys_documents
from sources.merx import build_merx_documents
import os
from langchain_ollama import OllamaEmbeddings

# Determine which source(s) to add
CANADABUYS = True
MERX = True

# Vector DB location
DB_LOCATION = "./chroma_langchain_db"

# Embedding model
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

def get_existing_sources(vector_store):
    """
    Check what unique sources exist in the vector database.
    Returns: set of source names (e.g., {'canadabuys', 'merx'})
    """
    if not os.path.exists(DB_LOCATION):
        return set()

    try:
        existing_docs = vector_store.get()
        existing_sources = set()

        if existing_docs and 'metadatas' in existing_docs:
            for metadata in existing_docs['metadatas']:
                if metadata and 'source' in metadata:
                    existing_sources.add(metadata['source'])

        return existing_sources
    except Exception as e:
        print(f"Error checking existing sources: {e}")
        return set()

def main():
    print("=== Building Vector Database ===")

    # Initialize vector store
    vector_store = initialize_vector_store("all_tenders", embeddings, DB_LOCATION)

    # Check what sources currently exist
    existing_sources = get_existing_sources(vector_store)
    print(f"Existing sources in database: {existing_sources if existing_sources else 'None (empty database)'}")

    # Determine what needs to be added
    sources_to_add = []
    if CANADABUYS and 'canadabuys' not in existing_sources:
        sources_to_add.append('canadabuys')
    if MERX and 'merx' not in existing_sources:
        sources_to_add.append('merx')

    if not sources_to_add:
        print("\nAll requested sources already exist in the database.")
        print("To rebuild, delete the database directory and run again.")
        return

    print(f"\nSources to add: {sources_to_add}")

    # Add CanadaBuys documents
    if 'canadabuys' in sources_to_add:
        print("\n--- Adding CanadaBuys documents ---")
        canadabuys_documents = build_canadabuys_documents()
        print(f"Built {len(canadabuys_documents)} CanadaBuys document chunks")
        populate_vector_db(vector_store, canadabuys_documents)
        print("CanadaBuys documents added successfully")

    # Add Merx documents
    if 'merx' in sources_to_add:
        print("\n--- Adding Merx documents ---")
        merx_documents = build_merx_documents()
        print(f"Built {len(merx_documents)} Merx document chunks")
        populate_vector_db(vector_store, merx_documents)
        print("Merx documents added successfully")

    # Final summary
    existing_sources = get_existing_sources(vector_store)
    print(f"\n=== Build Complete ===")
    print(f"Sources now in database: {existing_sources}")

if __name__ == "__main__":
    main()
