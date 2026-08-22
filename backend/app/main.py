from fastapi import FastAPI

app = FastAPI(
    title="Universal Web Data Extractor",
    description="API for extracting structured data from websites.",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "uwde-api",
        "version": "0.1.0",
    }