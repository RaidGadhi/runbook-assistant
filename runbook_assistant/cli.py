"""A CLI for retrieval and a real API smoke run."""

import argparse
import asyncio
import json
from pathlib import Path
from .models import AnalyzeRequest
from .service import Assistant


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve runbook context or analyze a short diagnostic sample."
    )
    parser.add_argument("mode", choices=["retrieve", "analyze"])
    parser.add_argument("logs", type=Path)
    parser.add_argument("--question", default="What should I investigate first?")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        request = AnalyzeRequest(logs=args.logs.read_text(), question=args.question)
        assistant = Assistant()
        result = (
            assistant.retrieve(request)
            if args.mode == "retrieve"
            else asyncio.run(assistant.analyze(request))
        )
    except Exception as exc:
        parser.exit(1, f"Error: {exc}\n")
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n")
        print(f"Saved {args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
