"""FastAPI application for the RAG lab.

The app can be built with an injected service (tests, local experiments) or
lazily build the production service from environment configuration.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from api.demo import DEMO_QUESTIONS
from api.eval_reports import read_eval_failures, read_eval_summary
from api.schemas import (
    BlockDetail,
    DemoQuestion,
    EvalFailure,
    EvalSummary,
    HealthResponse,
    QueryRequest,
)
from rag.service import (
    PROJECT_ROOT,
    RagService,
    UnknownTenantError,
    build_service_from_env,
)

API_VERSION = "0.1.0"


def default_reports_dir() -> Path:
    return Path(os.environ.get("EVAL_REPORTS_DIR", PROJECT_ROOT / "evals" / "reports"))


def create_app(
    service: RagService | None = None,
    *,
    reports_dir: str | Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Forge RAG Lab", version=API_VERSION)
    app.state.service = service
    app.state.reports_dir = Path(reports_dir) if reports_dir is not None else default_reports_dir()
    app.state.service_lock = threading.Lock()
    app.state.service_error = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            origin.strip()
            for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
            if origin.strip()
        ],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        try:
            rag_service = _get_service(request)
        except HTTPException:
            return HealthResponse(
                status="degraded",
                version=API_VERSION,
                qdrant="unknown",
                model_provider="unconfigured",
            )
        return HealthResponse(**rag_service.health())

    @app.post("/api/query")
    def query(req: QueryRequest, request: Request) -> dict:
        rag_service = _get_service(request)
        try:
            answer = rag_service.query(req.tenant_id, req.question, req.pipeline)
        except UnknownTenantError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return answer.model_dump(mode="json")

    @app.get("/api/demo/questions", response_model=list[DemoQuestion])
    def demo_questions() -> list[dict[str, str]]:
        return DEMO_QUESTIONS

    @app.get("/api/eval/summary", response_model=EvalSummary)
    def eval_summary(request: Request) -> dict:
        return read_eval_summary(Path(request.app.state.reports_dir))

    @app.get("/api/eval/failures", response_model=list[EvalFailure])
    def eval_failures(request: Request) -> list[dict]:
        return read_eval_failures(Path(request.app.state.reports_dir))

    @app.get(
        "/api/docs/{doc_id}/blocks/{block_id}",
        response_model=BlockDetail,
    )
    def document_block(
        doc_id: str,
        block_id: str,
        request: Request,
        tenant_id: str,
        version: str | None = None,
    ) -> BlockDetail:
        rag_service = _get_service(request)
        block = rag_service.get_block(
            tenant_id=tenant_id,
            doc_id=doc_id,
            block_id=block_id,
            version=version,
        )
        if block is None:
            raise HTTPException(status_code=404, detail="block not found")
        return BlockDetail(
            doc_id=block.doc_id,
            tenant_id=block.tenant_id,
            title=block.title,
            version=block.version,
            page=block.page,
            block_id=block.block_id,
            anchor=block.anchor,
            heading=block.heading,
            text=block.text,
        )

    return app


def _get_service(request: Request) -> RagService:
    current = request.app.state.service
    if current is not None:
        return current
    with request.app.state.service_lock:
        current = request.app.state.service
        if current is None:
            try:
                current = build_service_from_env()
            except Exception as exc:
                request.app.state.service_error = str(exc)
                raise HTTPException(
                    status_code=503,
                    detail=f"service unavailable: {type(exc).__name__}",
                ) from exc
            request.app.state.service = current
    return current


app = create_app()
