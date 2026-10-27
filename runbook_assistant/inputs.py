"""Keep stable line IDs while removing a few common credential formats."""

import re
from .models import Observation

# These checks reduce obvious exposure. They are not a complete DLP/injection
# defense. The API intentionally accepts short, reviewed diagnostic samples.
SECRET_PATTERNS = [
    re.compile(r"(?i)\bauthorization\s*[:=]\s*(?:bearer|basic)\s+[^\s,;]+"),
    re.compile(
        r"(?i)\b(?:password|passwd|token|api[_-]?key)\s*[:=]\s*(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
    ),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
]
INSTRUCTION_PATTERN = re.compile(
    r"ignore (?:all |the |any )?(?:previous|prior|system) instructions"
    r"|(?:system|developer)\s*(?:prompt|message)\s*:"
    r"|reveal (?:the )?(?:secret|key)"
    r"|<\|(?:system|im_start)\|>|\[INST\]",
    re.I,
)


def prepare_observations(logs: str) -> tuple[list[Observation], int]:
    if not logs.strip():
        raise ValueError("The diagnostic sample is empty.")
    if len(logs) > 16000:
        raise ValueError("The diagnostic sample exceeds 16,000 characters.")
    observations, redactions = [], 0
    for number, line in enumerate(filter(str.strip, logs.splitlines()), start=1):
        for pattern in SECRET_PATTERNS:
            line, count = pattern.subn("[REDACTED]", line)
            redactions += count
        observations.append(
            Observation(
                id=f"LOG-{number:03}",
                text=line,
                quarantined=bool(INSTRUCTION_PATTERN.search(line)),
            )
        )
    return observations, redactions
