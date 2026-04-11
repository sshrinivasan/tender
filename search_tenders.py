from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import initialize_vector_store, get_retriever
import os
from langchain_ollama import OllamaEmbeddings

# Determine which source(s) to search
CANADABUYS = False
MERX = True

# Vector DB location
DB_LOCATION = "./chroma_langchain_db"

# Model
model = OllamaLLM(model="llama3.2", options={"num_ctx": 8192})

# Embedding model
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Prompt template
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
    # Check if database exists
    if not os.path.exists(DB_LOCATION):
        print(f"Error: Vector database not found at {DB_LOCATION}")
        print("Please run build_vector_db.py first to create the database.")
        return

    print("=== Tender Search ===")

    # Initialize vector store
    vector_store = initialize_vector_store("all_tenders", embeddings, DB_LOCATION)

    # Build filter based on enabled sources
    enabled_sources = []
    if CANADABUYS:
        enabled_sources.append("canadabuys")
    if MERX:
        enabled_sources.append("merx")

    if not enabled_sources:
        print("Error: No sources are enabled (both CANADABUYS and MERX are False)")
        print("Please set at least one source to True in the script.")
        return

    print(f"Searching sources: {', '.join(enabled_sources)}")
    print("Type 'exit' or 'quit' to exit.\n")

    # User input loop
    while True:
        query = input("What kind of tenders are you looking for? ")
        if query.lower() in ["exit", "quit"]:
            print("Exiting the program.")
            break

        # Get the retriever with source filtering
        retriever = get_retriever(vector_store, source_filter=enabled_sources)

        # Retrieve relevant tenders
        retrieved_tenders = retriever.invoke(query)

        if not retrieved_tenders:
            print("No relevant tenders found for your query.\n")
            continue

        # Generate response
        result = chain.invoke({
            "user_query": query,
            "new_tenders": retrieved_tenders
        })

        print(f"\n{result}\n")

if __name__ == "__main__":
    main()
