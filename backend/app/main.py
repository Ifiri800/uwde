from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from backend.app.services.website_analyzer import analyze_website
from backend.app.services.http_fetcher import FetchError, fetch_url
from backend.app.services.extraction_engine import build_extraction_plan
from backend.app.services.extraction_executor import execute_extraction


app = FastAPI(
    title="Universal Web Data Extractor",
    description="API for extracting structured data from websites.",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: HttpUrl
    instruction: str


class ExtractRequest(BaseModel):
    url: HttpUrl
    instruction: str


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "uwde-api",
        "version": "0.1.0",
    }


@app.post("/api/analyze")
async def analyze_website_endpoint(request: AnalyzeRequest):
    instruction = request.instruction.strip()

    if not instruction:
        raise HTTPException(
            status_code=422,
            detail="Instruction is required.",
        )

    try:
        analysis = analyze_website(str(request.url))
    except FetchError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Website analysis failed: {exc}",
        ) from exc

    return {
        "status": "success",
        "url": analysis.url,
        "final_url": analysis.final_url,
        "status_code": analysis.status_code,
        "content_type": analysis.content_type,
        "title": analysis.title,
        "headings": analysis.headings,
        "paragraphs_count": analysis.paragraphs_count,
        "links_count": analysis.links_count,
        "images_count": analysis.images_count,
        "lists_count": analysis.lists_count,
        "tables_count": analysis.tables_count,
        "instruction": instruction,
    }


@app.post("/api/extract")
async def extract_website_endpoint(request: ExtractRequest):
    instruction = request.instruction.strip()

    if not instruction:
        raise HTTPException(
            status_code=422,
            detail="Instruction is required.",
        )

    try:
        plan = build_extraction_plan(instruction)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    try:
        fetched = fetch_url(str(request.url))
    except FetchError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Website fetch failed: {exc}",
        ) from exc

    try:
        html = fetched.body.decode("utf-8", errors="replace")

        result = execute_extraction(
            html=html,
            plan=plan,
            base_url=fetched.final_url,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction failed: {exc}",
        ) from exc

    return {
        "status": "success",
        "url": fetched.url,
        "final_url": fetched.final_url,
        "status_code": fetched.status_code,
        "content_type": fetched.content_type,
        "instruction": instruction,
        "plan": plan.to_dict(),
        "records": result.records,
        "record_count": len(result.records),
    }