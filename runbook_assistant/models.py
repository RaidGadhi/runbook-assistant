from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnalyzeRequest(StrictModel):
    logs: str = Field(min_length=1, max_length=16000)
    question: str = Field(
        default="What should I investigate first?", min_length=3, max_length=400
    )


class Observation(StrictModel):
    id: str
    text: str
    quarantined: bool


class ReferenceQuote(StrictModel):
    source_id: str
    quote: str


class Hypothesis(StrictModel):
    explanation: str
    observations: list[ReferenceQuote]
    runbooks: list[ReferenceQuote]


class ProposedCheck(StrictModel):
    command_id: str
    reason: str


class Analysis(StrictModel):
    decision: Literal["investigate", "needs_more_evidence"]
    summary: str
    hypotheses: list[Hypothesis]
    next_checks: list[ProposedCheck]
    missing_evidence: list[str]
    client_summary: str
