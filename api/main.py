from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Forge RAG Lab", version="0.1.0")


class QueryRequest(BaseModel):
    tenant_id: str
    question: str
    pipeline: Literal["fixed", "baseline"] = "fixed"


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "version": app.version,
        "qdrant": "unknown",
        "model_provider": "unconfigured",
    }


@app.post("/api/query")
def query(req: QueryRequest) -> dict:
    return {
        "answer": "Not implemented yet. The retrieval and generation pipeline is being built.",
        "abstained": True,
        "claims": [],
        "latency_ms": 0,
        "model": "none",
        "pipeline": req.pipeline,
        "trace_id": "stub",
    }
