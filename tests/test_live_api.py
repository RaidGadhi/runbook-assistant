"""Opt-in integration smoke test. Makes a real, billable API request."""

import asyncio
import json
import os
import unittest
from datetime import datetime, timezone
from runbook_assistant.models import AnalyzeRequest
from runbook_assistant.service import Assistant, ROOT


@unittest.skipUnless(
    os.getenv("RUN_LIVE_LLM_TEST") == "1" and os.getenv("OPENAI_API_KEY"),
    "Live API test requires OPENAI_API_KEY and RUN_LIVE_LLM_TEST=1.",
)
class LiveAPI(unittest.TestCase):
    def test_live_dns_smoke(self):
        result = asyncio.run(
            Assistant().analyze(
                AnalyzeRequest(
                    logs=(ROOT / "examples/dns.log").read_text(),
                    question="What does the DNS evidence support, and what remains unknown?",
                )
            )
        )
        self.assertEqual(result["mode"], "live")
        self.assertTrue(result["analysis"]["summary"])
        self.assertGreater(result["usage"]["input_tokens"], 0)
        self.assertTrue(result["response_id"])
        folder = ROOT / "reports"
        folder.mkdir(exist_ok=True)
        (folder / "live-smoke.json").write_text(
            json.dumps(
                {"executed_at": datetime.now(timezone.utc).isoformat(), **result},
                indent=2,
            )
            + "\n"
        )
