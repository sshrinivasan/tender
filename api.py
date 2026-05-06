from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from search import run_search
from tender_detail import fetch_and_summarize

app = FastAPI(title="Tender Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str
    source: str = "all"               # "merx" | "canadabuys" | "procuredata" | "all"
    closing_days: int | None = None   # 7 | 30 | None
    regions: list[str] | None = None  # e.g. ["Ontario", "NCR"]


@app.post("/search")
def search(req: SearchRequest):
    return run_search(req.query, req.source, req.closing_days, req.regions)


@app.get("/tender-detail")
def tender_detail(
    url: str = Query(...),
    source: str = Query(...),
    title: str = Query(""),
):
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    try:
        summary = fetch_and_summarize(url, source, title)
        return {"detail": summary}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
