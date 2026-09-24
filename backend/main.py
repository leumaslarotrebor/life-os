"""
LIFE OS — Backend
FastAPI application entry point.
"""

from fastapi import FastAPI

app = FastAPI(
    title="LIFE OS Backend",
    description="Agentic personal operating system — API layer.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict:
    """Health check — confirms the backend is running."""
    return {
        "status": "ok",
        "service": "life-os-backend",
    }
