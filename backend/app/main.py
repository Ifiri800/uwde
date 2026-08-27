from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from backend.app.config import get_settings
from backend.app.services.website_analyzer import analyze_website
from backend.app.services.http_fetcher import FetchError
from backend.app.services.pipeline_orchestrator import (
    run_extraction_pipeline,
)


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description="API for extracting structured data from websites.",
    version=settings.app_version,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
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
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/ready")
async def readiness_check():
    return {
        "status": "ready",
        "service": "uwde-api",
        "version": settings.app_version,
        "environment": settings.environment,
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
        result = run_extraction_pipeline(
            url=str(request.url),
            instruction=instruction,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except FetchError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Extraction pipeline failed: {exc}",
        ) from exc

    return result.to_dict()
