import { FormEvent, useMemo, useState } from "react";

type ReportResponse = {
  title: string;
  generated_at: string;
  prompt: string;
  executive_summary: string;
  key_findings: string[];
  recommendations: string[];
  action_plan: string[];
  report_markdown: string;
  download_filename: string;
  model: string;
  status: string;
};

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8000";

function downloadMarkdown(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function renderMarkdownPreview(report: ReportResponse | null) {
  if (!report) {
    return "<p>Your report preview will appear here.</p>";
  }

  return [
    `<h1>${report.title}</h1>`,
    `<p><strong>Generated:</strong> ${report.generated_at}</p>`,
    "<h2>Executive Summary</h2>",
    `<p>${report.executive_summary}</p>`,
    "<h2>Key Findings</h2>",
    `<ul>${report.key_findings.map((item) => `<li>${item}</li>`).join("")}</ul>`,
    "<h2>Recommendations</h2>",
    `<ul>${report.recommendations.map((item) => `<li>${item}</li>`).join("")}</ul>`,
    "<h2>Action Plan</h2>",
    `<ol>${report.action_plan.map((item) => `<li>${item}</li>`).join("")}</ol>`,
  ].join("");
}

export default function App() {
  const [prompt, setPrompt] = useState(
    "Generate a business report about the future of AI assistants in knowledge work.",
  );
  const [tone, setTone] = useState("professional");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<ReportResponse | null>(null);

  const previewHtml = useMemo(() => renderMarkdownPreview(report), [report]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${BACKEND_URL}/api/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, tone, audience: "decision makers" }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(
          body.detail || `Request failed with status ${response.status}`,
        );
      }

      setReport((await response.json()) as ReportResponse);
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Failed to generate report",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="intro panel">
        <div className="eyebrow">AI report generator</div>
        <h1>Chat with the app and export a downloadable report.</h1>
        <p>
          Type a prompt the way you would in ChatGPT. The backend uses your Groq
          key to generate a structured report, and the frontend gives you a
          clean preview plus a Markdown download.
        </p>
      </section>

      <section className="layout">
        <article className="panel">
          <h2>Prompt</h2>
          <form className="form" onSubmit={handleSubmit}>
            <label>
              Topic
              <textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                rows={7}
              />
            </label>

            <label>
              Tone
              <select
                value={tone}
                onChange={(event) => setTone(event.target.value)}
              >
                <option value="professional">Professional</option>
                <option value="concise">Concise</option>
                <option value="executive">Executive</option>
                <option value="technical">Technical</option>
              </select>
            </label>

            <div className="actions">
              <button type="submit" disabled={loading}>
                {loading ? "Generating..." : "Generate report"}
              </button>
              <button
                type="button"
                className="secondary"
                onClick={() =>
                  report &&
                  downloadMarkdown(
                    report.download_filename,
                    report.report_markdown,
                  )
                }
                disabled={!report}
              >
                Download report
              </button>
            </div>

            {error ? <p className="error">{error}</p> : null}
          </form>
        </article>

        <article className="panel preview">
          <h2>Report preview</h2>
          <div
            className="preview-content"
            dangerouslySetInnerHTML={{ __html: previewHtml }}
          />
          {report ? (
            <div className="meta">
              <span>Status: {report.status}</span>
              <span>Model: {report.model}</span>
            </div>
          ) : null}
        </article>
      </section>
    </main>
  );
}
