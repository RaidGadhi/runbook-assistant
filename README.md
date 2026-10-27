# Runbook Assistant

A small troubleshooting project by Raid Gadhi.

The app takes a short diagnostic sample, retrieves relevant sections from local
Markdown runbooks, and uses the OpenAI API to propose hypotheses and next checks.
It is built around Linux, shared storage, and Oracle standby troubleshooting.
The included transcripts are synthetic.

The backend is Python/FastAPI. The frontend is React, TypeScript, and Tailwind.
There is also a CLI, so the retrieval and analysis pipeline can be used without
the interface.

## What it does

- Assigns stable IDs to diagnostic lines.
- Redacts a few common credential formats and quarantines obvious embedded instructions.
- Uses BM25 to retrieve runbook sections.
- Requests structured JSON from an LLM.
- Checks citation IDs and quoted text against the supplied sources.
- Accepts next checks only from a reviewed command catalog.
- Reports token usage, latency, and validation repairs.

There are no predefined diagnoses for the example files. The model receives the
retrieved guidance and the prepared observations. The application never executes
the suggested commands.

## Run locally

Requirements: Python 3.12+ and Node.js 22.13+.

From the repository root:

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
source .venv/bin/activate
```

Install the backend, then build the frontend:

```bash
python -m pip install -e .
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn runbook_assistant.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. The API documentation is at
http://127.0.0.1:8000/docs.

**Find references** works without a model credential. It does not generate an
AI answer. For live analysis, set `OPENAI_API_KEY` in the server's environment
before starting it. `OPENAI_MODEL` defaults to `gpt-5.4-mini`.

For example, to enter a key without putting it in PowerShell history:

```powershell
$secureKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
python -m uvicorn runbook_assistant.api:app --host 127.0.0.1 --port 8000
```

Keep credentials out of Git. The server reads environment variables; it does
not automatically read a .env file.

During frontend development, run `npm run dev` inside `frontend` in a second
terminal. Vite proxies API requests to the local FastAPI server.

## CLI

```bash
python -m runbook_assistant.cli retrieve examples/dns.log
python -m runbook_assistant.cli analyze examples/dns.log --output reports/dns-live.json
```

The second command makes a real API request and requires a configured key.
The exported report contains prepared observations, selected sources, the
accepted analysis, and usage metadata.

## Tests

```bash
python -m unittest discover -s tests -v
```

The ordinary tests run without credentials. Provider tests use an injected HTTP
transport to exercise authentication failures, rate limits, truncation,
refusals, semantic repair, and the total request deadline.

The live integration smoke test is opt-in and billable:

```powershell
$env:RUN_LIVE_LLM_TEST = "1"
python -m unittest discover -s tests -p test_live_api.py -v
```

On Linux/macOS, set `RUN_LIVE_LLM_TEST=1` in the environment instead.
A successful run writes `reports/live-smoke.json`. This verifies the API path
and reference validation; it is not a diagnostic-accuracy benchmark.
The checked-in verification report records what was actually exercised.

## Code map

| File | Responsibility |
| --- | --- |
| `runbook_assistant/inputs.py` | Line IDs, redaction, instruction-pattern checks |
| `runbook_assistant/retrieval.py` | Markdown section index and BM25 ranking |
| `runbook_assistant/models.py` | Request and model-output schemas |
| `runbook_assistant/provider.py` | API request, retry budget, timeout, one repair |
| `runbook_assistant/validation.py` | Cross-reference and quotation checks |
| `runbook_assistant/service.py` | Pipeline orchestration and report assembly |
| `runbook_assistant/api.py` | Local HTTP API and built frontend |
| `runbook_assistant/cli.py` | Terminal entry point |

## Add a runbook

Add a Markdown file to `runbooks` with a title and `##` section headings.
Each section becomes a retrievable chunk, identified by filename and heading.
Keep sections below 2,400 characters.

To offer a new check, add a reviewed entry to `runbooks/commands.json` and
reference its section ID. The model selects command IDs; the backend supplies
the actual command text. Restart the server after changing the corpus.

## Container

```bash
docker build -t runbook-assistant .
docker run --rm -p 127.0.0.1:8000:8000 runbook-assistant
```

For live analysis, pass environment values using `--env-file .env`. The example
file documents the variable names. The Docker recipe is included; see the
verification report for whether it was exercised.

## Limits and development notes

This is a local prototype. Public deployment needs authentication, durable
request limits, and spend controls. The current input checks are pattern-based
and cannot detect every secret or prompt injection.

Quotation validation folds whitespace to handle wrapped Markdown. It still
checks the source ID and the actual words. A valid quotation does not prove
that the model's interpretation is correct.

The project was developed with AI-assisted coding. It uses authored runbook
notes and synthetic examples, with no employer or customer material.
Implementation decisions and a reproduced validation bug are documented in
[engineering notes](docs/engineering-notes.md).

## References

- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [systemd resolvectl manual](https://www.freedesktop.org/software/systemd/man/latest/resolvectl.html)
- [Oracle V$DATAGUARD_STATS](https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/V-DATAGUARD_STATS.html)
