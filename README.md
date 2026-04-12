# Tender Search

A local RAG (Retrieval-Augmented Generation) tool for searching Canadian government tenders. Currently supports [MERX](https://www.merx.com) and [CanadaBuys](https://canadabuys.canada.ca), with additional sources such as Alberta Purchasing in progress. Tender data is embedded into a local vector database and queried via a natural language interface powered by a local LLM.

## How it works

1. **Scrape** — collect MERX tender listings into local JSON via browser automation
2. **Fetch** — CanadaBuys tender data is downloaded live from the open.canada.ca API (no scraping needed)
3. **Build** — embed tender data from either or both sources into a local Chroma vector database
4. **Search** — query the database using natural language; a local LLM summarizes the results

## Scripts

### `utils/merx_scraper.py`

Scrapes tender listings from MERX using Playwright. On first run it opens a browser window for manual login; the auth session is saved to `merx_auth.json` for subsequent runs. Paginates through the solicitations table, saves raw HTML and parsed JSON per page, and writes a consolidated `data/merx/all_results.json`.

```bash
python utils/merx_scraper.py
```

### `build_vector_db.py`

Loads tender data from one or both sources, converts each tender into chunked `Document` objects, and upserts them into a local Chroma vector database at `./chroma_langchain_db`. Skips sources that are already present to avoid duplicates.

- **CanadaBuys** — fetched live from the [open.canada.ca](https://open.canada.ca) API as a CSV; no prior scraping needed
- **MERX** — read from `data/merx/all_results.json` produced by `merx_scraper.py`

```bash
python build_vector_db.py
```

### `search_tenders.py`

Interactive CLI for querying the vector database. Embeds the user's query, retrieves the most relevant tenders via similarity search, and passes them to a local `llama3.2` model to generate a formatted summary. Can search across either or both sources.

```bash
python search_tenders.py
```

## Dependencies

- [Playwright](https://playwright.dev/python/) — browser automation for scraping
- [LangChain](https://python.langchain.com/) — document pipeline and retrieval chain
- [Chroma](https://www.trychroma.com/) — local vector store
- [Ollama](https://ollama.com/) — local LLM and embedding model runner
  - Embedding model: `mxbai-embed-large`
  - LLM: `llama3.2`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt  # or use the virtual env in tender_env/

# Pull required Ollama models
ollama pull mxbai-embed-large
ollama pull llama3.2

# Scrape MERX (requires a MERX account)
python utils/merx_scraper.py

# Build the vector database
python build_vector_db.py

# Search
python search_tenders.py
```
