# Engineering notes

## Retrieval

The corpus has eight short Markdown sections. BM25 is enough to inspect the
ranking and run everything without an embedding service or vector database.
It has a clear limitation: terminology and paraphrases can produce weak matches.
The retriever limits results and drops weak matches relative to the best score.
An unrelated query can return no context.

Each report includes a corpus fingerprint covering the Markdown and command
catalog. This identifies the guidance used for that report.

## JSON validation and evidence validation

A structurally valid response can still cite text from the wrong log line,
omit evidence, or propose an unknown check. Pydantic handles the JSON shape.
The second validation step checks the references against the actual context.

The test `test_schema_only_can_accept_missing_evidence` demonstrates the
difference: the response passes Pydantic but fails the evidence check.

The model selects command IDs from the supplied catalog. The server resolves
the IDs to reviewed command text; it does not execute anything.

## A reproduced formatting bug

The first quotation validator used a direct substring comparison. A valid
quotation failed when the original Markdown wrapped a sentence across lines
but the quotation used spaces.

The regression test
`test_wrapped_runbook_quote_matches_after_whitespace_normalization` reproduced
that failure. The fix normalizes whitespace on both sides before comparison.
Unknown source IDs and quotations containing different words still fail.

This was reproduced in the deterministic test harness. It is not presented as
an observed live-model incident.

## Provider failure handling

The provider has a total 25-second deadline, one shared transport retry for
429/502/503 responses, and at most one validation repair. The maximum is three
HTTP attempts: one initial request, one transport retry, and one repair.

A long Retry-After value fails promptly. Authentication errors, refusals, and
truncated responses fail explicitly. A rejected response is not displayed as an
accepted analysis. Token totals accumulate across completed response attempts.

## Verification boundary

HTTP transport tests verify how the adapter behaves with controlled responses.
They do not show that a particular live model is diagnostically accurate.
The opt-in integration test records an actual API response and its usage once
a credential is configured.
