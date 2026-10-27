"""Validate reference integrity separately from JSON shape."""

from .models import Analysis, Observation


def normalized(text: str) -> str:
    return " ".join(text.split())


class AnalysisValidationError(ValueError):
    def __init__(self, issues: list[str]):
        self.issues = issues
        super().__init__("; ".join(issues))


def validate_analysis(
    analysis: Analysis,
    observations: list[Observation],
    sources: list[dict],
    commands: list[dict],
) -> None:
    issues = []
    logs = {o.id: o.text for o in observations if not o.quarantined}
    runbooks = {s["id"]: s["text"] for s in sources}
    available = {c["id"]: c for c in commands}
    if not 20 <= len(analysis.summary) <= 1400:
        issues.append("Summary must be between 20 and 1400 characters.")
    if (
        not 10 <= len(analysis.client_summary) <= 900
        or len(analysis.client_summary.split()) > 100
    ):
        issues.append(
            "Client summary must be under 100 words and within the text limit."
        )
    if (
        len(analysis.hypotheses) > 3
        or len(analysis.next_checks) > 5
        or len(analysis.missing_evidence) > 6
    ):
        issues.append("Too many hypotheses, checks, or missing-evidence questions.")
    if analysis.decision == "investigate" and not analysis.hypotheses:
        issues.append(
            "An investigation decision needs at least one cited provisional hypothesis."
        )
    if analysis.decision == "needs_more_evidence" and not analysis.missing_evidence:
        issues.append("An abstaining answer must say which evidence is missing.")
    if not any(analysis.hypotheses) and not analysis.missing_evidence:
        issues.append(
            "The answer must provide cited hypotheses or request missing evidence."
        )
    for i, hypothesis in enumerate(analysis.hypotheses):
        if not 15 <= len(hypothesis.explanation) <= 900:
            issues.append(f"Hypothesis {i + 1} has an invalid explanation length.")
        if not hypothesis.observations or not hypothesis.runbooks:
            issues.append(
                f"Hypothesis {i + 1} needs observation and runbook citations."
            )
        if len(hypothesis.observations) > 5 or len(hypothesis.runbooks) > 3:
            issues.append(f"Hypothesis {i + 1} has too many citations.")
        for kind, references, allowed in [
            ("log", hypothesis.observations, logs),
            ("runbook", hypothesis.runbooks, runbooks),
        ]:
            for reference in references:
                text = allowed.get(reference.source_id)
                if text is None:
                    issues.append(
                        f"Unknown or excluded {kind} citation: {reference.source_id}."
                    )
                elif len(normalized(reference.quote)) < 8 or normalized(
                    reference.quote
                ) not in normalized(text):
                    issues.append(f"Quote does not match source {reference.source_id}.")
    used_commands = set()
    for proposed in analysis.next_checks:
        command = available.get(proposed.command_id)
        if not command:
            issues.append(f"Unknown command ID: {proposed.command_id}.")
        elif command["source_id"] not in runbooks:
            issues.append(
                f"Command {proposed.command_id} is not supported by retrieved guidance."
            )
        if proposed.command_id in used_commands:
            issues.append(f"Duplicate command ID: {proposed.command_id}.")
        used_commands.add(proposed.command_id)
        if not 10 <= len(proposed.reason) <= 500:
            issues.append(f"Invalid reason for check {proposed.command_id}.")
    if any(not 5 <= len(question) <= 300 for question in analysis.missing_evidence):
        issues.append("A missing-evidence question is empty or too long.")
    if issues:
        raise AnalysisValidationError(issues)
