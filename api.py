from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from search import run_search

app = FastAPI(title="Tender Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    source: str = "both"              # "merx" | "canadabuys" | "both"
    closing_days: int | None = None   # 7 | 30 | None
    regions: list[str] | None = None  # e.g. ["Ontario", "NCR"]


@app.post("/search")
def search(req: SearchRequest):
    return run_search(req.query, req.source, req.closing_days, req.regions)
