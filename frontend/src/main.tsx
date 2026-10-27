import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

type Quote = { source_id: string; quote: string };
type Analysis = {
  decision: "investigate" | "needs_more_evidence";
  summary: string;
  client_summary: string;
  hypotheses: {
    explanation: string;
    observations: Quote[];
    runbooks: Quote[];
  }[];
  next_checks: { command_id: string; reason: string }[];
  missing_evidence: string[];
};
type Report = {
  mode: string;
  sources: { id: string; title: string; text: string; score: number }[];
  observations: { id: string; text: string; quarantined: boolean }[];
  commands: {
    id: string;
    label: string;
    command: string;
    expected: string;
    source_id: string;
  }[];
  redactions: number;
  quarantined: number;
  corpus_fingerprint: string;
  retrieval_ms: number;
  analysis?: Analysis;
  usage?: { input_tokens: number; output_tokens: number; repairs: number };
  model?: string;
  total_ms?: number;
};
function App() {
  const [logs, setLogs] = useState("");
  const [question, setQuestion] = useState(
    "What should I investigate first, and what evidence is missing?",
  );
  const [examples, setExamples] = useState<{ name: string; logs: string }[]>(
    [],
  );
  const [health, setHealth] = useState<{
    model_configured: boolean;
    model: string;
    runbook_sections: number;
  } | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [pending, setPending] = useState("");
  const [error, setError] = useState("");
  const [audience, setAudience] = useState("engineer");
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok) throw new Error();
        setHealth(await r.json());
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Could not reach the API. Start the FastAPI server and refresh.",
          );
      });
    fetch("/api/examples", { signal: controller.signal })
      .then(async (r) => {
        if (!r.ok) return;
        const data = (await r.json()) as { name: string; logs: string }[];
        setExamples(data);
        const dns = data.find((e) => e.name === "Dns");
        if (dns) setLogs(dns.logs);
      })
      .catch(() => {});
    return () => controller.abort();
  }, []);
  async function run(mode: "retrieve" | "analyze") {
    setPending(mode);
    setError("");
    setReport(null);
    try {
      const response = await fetch("/api/" + mode, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ logs, question }),
      });
      const data = (await response.json()) as Report & {
        error?: string;
        detail?: { msg: string }[];
      };
      if (!response.ok)
        throw new Error(
          data.error || data.detail?.[0]?.msg || "The request failed.",
        );
      setReport(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request failed.");
    } finally {
      setPending("");
    }
  }
  function exportReport() {
    if (!report) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(report, null, 2)], { type: "application/json" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "runbook-report.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  const apiLabel = health
    ? health.runbook_sections +
      " runbook sections · " +
      (health.model_configured
        ? health.model
        : "API key not configured; retrieval works without one")
    : "Checking API connection…";
  const resultLabel = report?.usage
    ? report.model +
      " · " +
      (report.usage.input_tokens + report.usage.output_tokens) +
      " tokens · " +
      report.usage.repairs +
      " repairs · " +
      report.total_ms?.toFixed(0) +
      " ms"
    : report
      ? "Retrieval " +
        report.retrieval_ms.toFixed(1) +
        " ms · corpus " +
        report.corpus_fingerprint
      : "";
  return (
    <div className="mx-auto max-w-6xl px-5 py-8 md:px-9 md:py-12">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Runbook Assistant
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Python / FastAPI / retrieval / OpenAI API
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Raid Gadhi · Personal project</p>
          <a
            href="/docs"
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block underline underline-offset-4"
          >
            API documentation
          </a>
        </div>
      </header>
      <p className="mb-6 max-w-2xl text-sm leading-7 text-slate-600">
        Paste a short diagnostic sample. Retrieve the relevant runbook sections,
        then ask the model for a provisional explanation and the next checks.
        Every hypothesis must quote its sources.
      </p>
      <div className="grid items-start gap-6 lg:grid-cols-[1.1fr_1fr]">
        <section className="rounded-lg border border-slate-200 bg-white p-5">
          <div className="mb-5 flex items-center justify-between gap-4">
            <h2 className="font-medium">Diagnostic sample</h2>
            <select
              aria-label="Load a synthetic example"
              defaultValue=""
              disabled={!!pending}
              onChange={(e) => {
                const example = examples.find((x) => x.name === e.target.value);
                if (example) {
                  setLogs(example.logs);
                  setReport(null);
                  setError("");
                }
              }}
              className="max-w-48 rounded border border-slate-200 px-2 py-1.5 text-xs"
            >
              <option value="" disabled>
                Load a synthetic example
              </option>
              {examples.map((e) => (
                <option key={e.name}>{e.name}</option>
              ))}
            </select>
          </div>
          <label
            htmlFor="question"
            className="mb-2 block text-xs font-medium text-slate-600"
          >
            Question
          </label>
          <input
            id="question"
            value={question}
            disabled={!!pending}
            maxLength={400}
            onChange={(e) => {
              setQuestion(e.target.value);
              setReport(null);
            }}
            className="mb-5 w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
          <label
            htmlFor="logs"
            className="mb-2 block text-xs font-medium text-slate-600"
          >
            Logs or command output
          </label>
          <textarea
            id="logs"
            value={logs}
            disabled={!!pending}
            maxLength={16000}
            onChange={(e) => {
              setLogs(e.target.value);
              setReport(null);
            }}
            spellCheck={false}
            className="h-80 w-full resize-y rounded border border-slate-300 bg-slate-50 p-3 font-mono text-xs leading-6"
          />
          <p className="mt-2 text-xs leading-5 text-slate-500">
            Examples are synthetic. Review any pasted data before using live
            analysis. The app never executes the displayed commands.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button
              disabled={!!pending || !logs.trim()}
              onClick={() => run("retrieve")}
              className="rounded border border-slate-300 px-4 py-2.5 text-sm font-medium hover:bg-slate-50"
            >
              {pending === "retrieve" ? "Retrieving…" : "Find references"}
            </button>
            <button
              disabled={!!pending || !logs.trim() || !health?.model_configured}
              title={
                !health?.model_configured
                  ? "Configure OPENAI_API_KEY on the server first"
                  : undefined
              }
              onClick={() => run("analyze")}
              className="rounded bg-slate-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
            >
              {pending === "analyze" ? "Analyzing…" : "Analyze with LLM"}
            </button>
          </div>
          <p className="mt-4 text-xs text-slate-500">{apiLabel}</p>
        </section>
        <div className="space-y-5" aria-live="polite">
          {error && (
            <div
              role="alert"
              className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-800"
            >
              {error}
            </div>
          )}
          {!report && (
            <section className="rounded-lg border border-dashed border-slate-300 p-6">
              <h2 className="text-sm font-medium">
                {pending
                  ? "Working on the sample…"
                  : "Start with the references"}
              </h2>
              <p className="mt-3 text-sm leading-7 text-slate-500">
                {pending
                  ? "The result will appear here when the request completes."
                  : "Find references runs the input checks and retrieves Markdown sections. It does not call an LLM. Analyze with LLM adds a live model response and validates its source quotations."}
              </p>
            </section>
          )}
          {report?.analysis && (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="mb-4 flex items-center justify-between gap-3">
                <h2 className="font-medium">Analysis</h2>
                <span className="rounded bg-blue-50 px-2 py-1 text-[11px] text-blue-700">
                  {report.analysis.decision === "investigate"
                    ? "Provisional hypotheses"
                    : "More evidence needed"}
                </span>
              </div>
              <div className="mb-4 flex gap-4 text-xs">
                <button
                  className={
                    audience === "engineer"
                      ? "font-semibold underline underline-offset-4"
                      : "text-slate-500"
                  }
                  onClick={() => setAudience("engineer")}
                >
                  Engineer
                </button>
                <button
                  className={
                    audience === "client"
                      ? "font-semibold underline underline-offset-4"
                      : "text-slate-500"
                  }
                  onClick={() => setAudience("client")}
                >
                  Client explanation
                </button>
              </div>
              <p className="text-sm leading-7 text-slate-700">
                {audience === "client"
                  ? report.analysis.client_summary
                  : report.analysis.summary}
              </p>
              {audience === "engineer" &&
                report.analysis.hypotheses.map((h, i) => (
                  <article
                    key={i}
                    className="mt-5 border-t border-slate-100 pt-4"
                  >
                    <h3 className="mb-2 text-xs font-semibold text-slate-500">
                      HYPOTHESIS {i + 1}
                    </h3>
                    <p className="text-sm leading-7">{h.explanation}</p>
                    {[...h.observations, ...h.runbooks].map((q, j) => (
                      <blockquote
                        key={j}
                        className="mt-3 border-l-2 border-slate-200 pl-3 text-xs leading-6 text-slate-600"
                      >
                        <span className="block font-mono text-[10px] text-slate-500">
                          {q.source_id}
                        </span>
                        “{q.quote}”
                      </blockquote>
                    ))}
                  </article>
                ))}
              {!!report.analysis.missing_evidence.length && (
                <div className="mt-5 border-t border-slate-100 pt-4">
                  <h3 className="mb-2 text-xs font-semibold text-slate-500">
                    MISSING EVIDENCE
                  </h3>
                  <ul className="ml-4 list-disc space-y-2 text-sm leading-6 text-slate-600">
                    {report.analysis.missing_evidence.map((q, i) => (
                      <li key={i}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
              {!!report.analysis.next_checks.length && (
                <div className="mt-5 border-t border-slate-100 pt-4">
                  <h3 className="mb-3 text-xs font-semibold text-slate-500">
                    NEXT CHECKS · OPERATOR REVIEW
                  </h3>
                  {report.analysis.next_checks.map((check, i) => {
                    const c = report.commands.find(
                      (c) => c.id === check.command_id,
                    )!;
                    return (
                      <div key={i} className="mb-4">
                        <p className="text-sm font-medium">{c.label}</p>
                        <code className="my-2 block overflow-x-auto rounded bg-slate-100 px-3 py-2 text-xs">
                          {c.command}
                        </code>
                        <p className="text-xs leading-6 text-slate-600">
                          {check.reason}
                        </p>
                        <p className="mt-1 font-mono text-[10px] text-slate-400">
                          {c.source_id}
                        </p>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>
          )}
          {report && (
            <section className="rounded-lg border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between gap-3">
                <h2 className="font-medium">Retrieved context</h2>
                <span className="text-xs text-slate-500">
                  {report.mode === "live"
                    ? "Live model used"
                    : "Retrieval only · no model called"}
                </span>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                {report.sources.length} sections · {report.redactions}{" "}
                redactions · {report.quarantined} quarantined entries
              </p>
              {!report.sources.length && (
                <p className="mt-4 text-sm text-slate-600">
                  No relevant guidance matched. Add a runbook or ask a more
                  specific question.
                </p>
              )}
              {report.sources.map((s) => (
                <details
                  key={s.id}
                  className="mt-4 border-t border-slate-100 pt-3"
                >
                  <summary className="cursor-pointer text-sm font-medium">
                    {s.title}
                    <span className="mt-1 block font-mono text-[10px] font-normal text-slate-500">
                      {s.id + " · BM25 " + s.score}
                    </span>
                  </summary>
                  <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-slate-600">
                    {s.text}
                  </p>
                </details>
              ))}
            </section>
          )}
          {report && (
            <details className="rounded-lg border border-slate-200 bg-white p-5">
              <summary className="cursor-pointer text-sm font-medium">
                Inspect prepared observations
              </summary>
              <div className="mt-4 space-y-3">
                {report.observations.map((o) => (
                  <div
                    key={o.id}
                    className={o.quarantined ? "rounded bg-amber-50 p-2" : ""}
                  >
                    <span className="font-mono text-[10px] text-slate-500">
                      {o.id + (o.quarantined ? " · quarantined" : "")}
                    </span>
                    <pre className="mt-1 whitespace-pre-wrap break-words font-mono text-xs leading-6 text-slate-600">
                      {o.text}
                    </pre>
                  </div>
                ))}
              </div>
            </details>
          )}
          {report && (
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500">
              <span>{resultLabel}</span>
              <button
                onClick={exportReport}
                className="underline underline-offset-4"
              >
                Export JSON
              </button>
            </div>
          )}
        </div>
      </div>
      <footer className="mt-9 border-t border-slate-200 pt-4 text-xs leading-6 text-slate-500">
        Citation checks verify quoted sources after whitespace normalization.
        Review the interpretation before using it.
      </footer>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
