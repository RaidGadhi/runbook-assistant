"""Markdown sections + BM25. The corpus is small enough to index in memory."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import math
import re

STOPWORDS = set(
    "a an the is are was were and or to of in on for from by with it this that be as at not".split()
)


@dataclass(frozen=True)
class Chunk:
    id: str
    title: str
    text: str
    file: str


def terms(text: str) -> list[str]:
    return [
        t
        for t in re.findall(r"[a-z0-9]+", text.lower())
        if len(t) > 1 and t not in STOPWORDS
    ]


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


class RunbookIndex:
    def __init__(self, directory: Path):
        self.chunks: list[Chunk] = []
        digest = hashlib.sha256()
        for path in sorted(directory.glob("*.md")):
            raw = path.read_text(encoding="utf-8")
            digest.update(path.name.encode() + b"\0" + raw.encode())
            title = next(
                (
                    line[2:].strip()
                    for line in raw.splitlines()
                    if line.startswith("# ")
                ),
                path.stem,
            )
            sections = re.split(r"(?m)^## ", raw)
            for section in sections[1:]:
                heading, _, body = section.partition("\n")
                text = body.strip()
                if not text:
                    continue
                if len(text) > 2400:
                    raise ValueError(
                        f"Runbook section is too large: {path.name} / {heading}"
                    )
                self.chunks.append(
                    Chunk(
                        id=f"{path.stem}/{slug(heading)}",
                        title=f"{title} / {heading.strip()}",
                        text=text,
                        file=path.name,
                    )
                )
        if not self.chunks:
            raise ValueError("No runbook sections found.")
        if len({c.id for c in self.chunks}) != len(self.chunks):
            raise ValueError("Runbook headings produce duplicate source IDs.")
        command_file = directory / "commands.json"
        self.commands = json.loads(command_file.read_text(encoding="utf-8"))
        digest.update(command_file.read_bytes())
        chunk_ids = {c.id for c in self.chunks}
        if len({c["id"] for c in self.commands}) != len(self.commands):
            raise ValueError("Duplicate command IDs.")
        for command in self.commands:
            if command["source_id"] not in chunk_ids or not command.get("read_only"):
                raise ValueError(f"Unreviewed command reference: {command['id']}")
        self.fingerprint = digest.hexdigest()[:16]
        self.tokens = [terms(chunk.title + " " + chunk.text) for chunk in self.chunks]
        self.average_length = sum(map(len, self.tokens)) / len(self.tokens)

    def search(self, query: str, limit: int = 4) -> list[dict]:
        scored = []
        for chunk, words in zip(self.chunks, self.tokens):
            score = 0.0
            for term in set(terms(query)):
                frequency = words.count(term)
                if not frequency:
                    continue
                document_frequency = sum(term in document for document in self.tokens)
                inverse_frequency = math.log(
                    1
                    + (len(self.chunks) - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                score += (
                    inverse_frequency
                    * frequency
                    * 2.2
                    / (
                        frequency
                        + 1.2 * (0.25 + 0.75 * len(words) / self.average_length)
                    )
                )
            if score > 0:
                scored.append(
                    {
                        "id": chunk.id,
                        "title": chunk.title,
                        "text": chunk.text,
                        "file": chunk.file,
                        "score": round(score, 3),
                    }
                )
        scored.sort(key=lambda item: (-item["score"], item["id"]))
        # Drop weak matches rather than always spending the whole context budget.
        cutoff = scored[0]["score"] * 0.30 if scored else 0
        return [item for item in scored if item["score"] >= cutoff][:limit]

    def available_commands(self, source_ids: set[str]) -> list[dict]:
        return [c for c in self.commands if c["source_id"] in source_ids]
