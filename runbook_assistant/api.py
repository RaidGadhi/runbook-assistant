"""Local API. The default run command binds to 127.0.0.1."""

from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .models import AnalyzeRequest
from .provider import ProviderError
from .service import Assistant, ROOT

app = FastAPI(title="Runbook Assistant", version="0.1.0")
assistant = Assistant()


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.url.path.startswith("/api/") and request.method == "POST":
        origin = request.headers.get("origin")
        if origin and origin not in {
            str(request.base_url).rstrip("/"),
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        }:
            return JSONResponse(
                {"error": "Request origin is not allowed.", "code": "origin_rejected"},
                status_code=403,
            )
        if "application/json" not in request.headers.get("content-type", ""):
            return JSONResponse(
                {"error": "Send a JSON body.", "code": "content_type"}, status_code=415
            )
        if len(await request.body()) > 24000:
            return JSONResponse(
                {"error": "Request body is too large.", "code": "input_limit"},
                status_code=413,
            )
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ProviderError)
async def provider_error(request: Request, exc: ProviderError):
    status = (
        503
        if exc.code == "not_configured"
        else 504
        if exc.code == "provider_timeout"
        else 422
        if exc.code == "no_context"
        else 502
    )
    return JSONResponse(
        {"error": str(exc), "code": exc.code},
        status_code=status,
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(ValueError)
async def invalid_sample(request: Request, exc: ValueError):
    return JSONResponse(
        {"error": str(exc), "code": "invalid_sample"},
        status_code=422,
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        "runbook_sections": len(assistant.index.chunks),
        "corpus_fingerprint": assistant.index.fingerprint,
    }


@app.get("/api/examples")
def examples():
    return [
        {"name": p.stem.replace("-", " ").title(), "logs": p.read_text()}
        for p in sorted((ROOT / "examples").glob("*.log"))
    ]


@app.post("/api/retrieve")
def retrieve(request: AnalyzeRequest):
    return assistant.retrieve(request)


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    return await assistant.analyze(request)


frontend = ROOT / "frontend" / "dist"
if frontend.is_dir():
    app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
