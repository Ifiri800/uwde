from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl


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


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "uwde-api",
        "version": "0.1.0",
    }


@app.post("/api/analyze")
async def analyze_website(request: AnalyzeRequest):
    return {
        "status": "success",
        "url": str(request.url),
        "instruction": request.instruction,
        "message": "Website analysis request received.",
    }