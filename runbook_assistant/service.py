from __future__ import annotations
from pathlib import Path
import hashlib
import os
import time
from .inputs import prepare_observations
from .models import AnalyzeRequest
from .provider import ProviderError, generate
from .retrieval import RunbookIndex
from .validation import validate_analysis

ROOT = Path(__file__).resolve().parents[1]


class Assistant:
    def __init__(self, runbooks: Path | None = None):
        self.index = RunbookIndex(runbooks or ROOT / "runbooks")

    def retrieve(self, request: AnalyzeRequest) -> dict:
        start = time.perf_counter()
        observations, redactions = prepare_observations(request.logs)
        trusted = [o for o in observations if not o.quarantined]
        if not trusted:
            raise ValueError("No usable observations remain after input checks.")
        query = request.question + "\n" + "\n".join(o.text for o in trusted)
        sources = self.index.search(query)
        commands = self.index.available_commands({s["id"] for s in sources})
        return {
            "mode": "retrieval_only",
            "observations": [o.model_dump() for o in observations],
            "sources": sources,
            "commands": commands,
            "redactions": redactions,
            "quarantined": sum(o.quarantined for o in observations),
            "corpus_fingerprint": self.index.fingerprint,
            "input_fingerprint": hashlib.sha256(query.encode()).hexdigest()[:16],
            "retrieval_ms": round((time.perf_counter() - start) * 1000, 2),
        }

    async def analyze(
        self,
        request: AnalyzeRequest,
        *,
        api_key: str | None = None,
        model: str | None = None,
        transport=None,
    ) -> dict:
        started = time.perf_counter()
        prepared = self.retrieve(request)
        key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        if not key:
            raise ProviderError(
                "Set OPENAI_API_KEY on the server to run an LLM analysis. Retrieval-only mode works without a key.",
                "not_configured",
            )
        if not prepared["sources"]:
            raise ProviderError(
                "No relevant runbook sections matched. Add appropriate guidance or ask a more specific question.",
                "no_context",
            )
        observations, _ = prepare_observations(request.logs)
        context = {
            "question": request.question,
            "observations": [
                o.model_dump(exclude={"quarantined"})
                for o in observations
                if not o.quarantined
            ],
            "runbook_sections": [
                {k: s[k] for k in ["id", "title", "text"]} for s in prepared["sources"]
            ],
            "command_catalog": prepared["commands"],
        }
        response = await generate(
            context,
            api_key=key,
            model=model or os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            validator=lambda analysis: validate_analysis(
                analysis, observations, prepared["sources"], prepared["commands"]
            ),
            transport=transport,
        )
        chosen = {check.command_id for check in response["analysis"].next_checks}
        return {
            **prepared,
            "mode": "live",
            "analysis": response["analysis"].model_dump(),
            "selected_commands": [c for c in prepared["commands"] if c["id"] in chosen],
            "model": response["model"],
            "response_id": response["response_id"],
            "usage": response["usage"],
            "context_characters": response["context_characters"],
            "total_ms": round((time.perf_counter() - started) * 1000, 2),
            "validation": "JSON shape, citation IDs, exact quotations, and command references passed. Interpretation still requires review.",
        }
