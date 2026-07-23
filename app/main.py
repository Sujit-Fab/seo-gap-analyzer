"""
SEO Content Gap Analyzer — a small FastAPI service.

POST /analyze     -> run a content+keyword pair through the LLM gap analysis
GET  /analyze/{id} -> fetch a previously saved analysis

Run locally:
    uvicorn app.main:app --reload
Then visit http://127.0.0.1:8000/docs for interactive API docs.
"""

from fastapi import FastAPI, HTTPException

from app.firestore_service import get_analysis, save_analysis
from app.llm_service import analyze_content
from app.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="SEO Content Gap Analyzer",
    description="Finds content gaps against a target keyword using an LLM, stores results in Firestore.",
    version="0.1.0",
)


@app.get("/")
def health_check():
    return {"status": "ok", "service": "seo-content-gap-analyzer"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    result = analyze_content(request.content, request.target_keyword)
    save_analysis(result)
    return result


@app.get("/analyze/{analysis_id}")
def get_saved_analysis(analysis_id: str):
    result = get_analysis(analysis_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result
