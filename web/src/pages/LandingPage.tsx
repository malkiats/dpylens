import React, { useMemo, useState } from "react";
import {
  Activity,
  BrainCircuit,
  ChevronRight,
  Code2,
  FlaskConical,
  Share2,
  ShieldCheck,
  Terminal
} from "lucide-react";
import { analyzeRepo, downloadUrlAbsolute, reportUrlAbsolute, type AnalyzeResponse } from "../lib/api";

type ThemeColor = "blue" | "cyan" | "orange" | "teal" | "indigo" | "amber";

type Feature = {
  title: string;
  subtitle: string;
  items: string[];
  color: ThemeColor;
  icon: React.ComponentType<{ className?: string }>;
  ready: boolean;
};

function circuitDataUri() {
  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640">
    <defs>
      <pattern id="p" width="80" height="80" patternUnits="userSpaceOnUse">
        <path d="M10 10 H70 V70 H10 Z" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
        <path d="M10 40 H70" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
        <path d="M40 10 V70" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
        <circle cx="10" cy="10" r="2" fill="rgba(255,255,255,0.10)"/>
        <circle cx="70" cy="70" r="2" fill="rgba(255,255,255,0.10)"/>
        <circle cx="40" cy="40" r="2" fill="rgba(34,211,238,0.14)"/>
        <path d="M40 40 C55 40, 55 25, 70 25" fill="none" stroke="rgba(34,211,238,0.10)" stroke-width="1"/>
        <circle cx="70" cy="25" r="2" fill="rgba(34,211,238,0.12)"/>
      </pattern>
      <radialGradient id="g" cx="50%" cy="50%" r="70%">
        <stop offset="0%" stop-color="rgba(34,211,238,0.10)"/>
        <stop offset="60%" stop-color="rgba(99,102,241,0.06)"/>
        <stop offset="100%" stop-color="rgba(0,0,0,0)"/>
      </radialGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#g)"/>
    <rect width="100%" height="100%" fill="url(#p)"/>
  </svg>
  `.trim();

  return `data:image/svg+xml,${encodeURIComponent(svg)}`;
}

function badge(text: string) {
  return (
    <span className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] uppercase tracking-widest text-gray-300">
      {text}
    </span>
  );
}

function colorClasses(color: ThemeColor) {
  switch (color) {
    case "blue":
      return { border: "border-blue-500/40", glowBg: "bg-blue-500/10", text: "text-blue-300" };
    case "cyan":
      return { border: "border-cyan-500/40", glowBg: "bg-cyan-500/10", text: "text-cyan-300" };
    case "orange":
      return { border: "border-orange-500/40", glowBg: "bg-orange-500/10", text: "text-orange-300" };
    case "teal":
      return { border: "border-teal-500/40", glowBg: "bg-teal-500/10", text: "text-teal-300" };
    case "indigo":
      return { border: "border-indigo-500/40", glowBg: "bg-indigo-500/10", text: "text-indigo-300" };
    case "amber":
      return { border: "border-amber-500/40", glowBg: "bg-amber-500/10", text: "text-amber-300" };
  }
}

function FeatureCard(props: Feature) {
  const cls = colorClasses(props.color);
  return (
    <div
      className={[
        "group relative flex h-full flex-col overflow-hidden rounded-2xl",
        "bg-white/[0.06] backdrop-blur-md border shadow-[0_25px_80px_rgba(0,0,0,0.55)]",
        "transition-all duration-300 hover:bg-white/[0.08]",
        cls.border
      ].join(" ")}
    >
      <div
        className={[
          "pointer-events-none absolute -top-20 -right-20 h-48 w-48 rounded-full blur-3xl transition-all duration-500",
          cls.glowBg,
          "opacity-50 group-hover:opacity-80"
        ].join(" ")}
      />
      <div className="relative p-6">
        <div className="flex items-start justify-between gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl border border-white/10 bg-black/30 shadow-inner shadow-black/40">
            <props.icon className={["h-6 w-6", cls.text].join(" ")} />
          </div>
          {!props.ready ? badge("Coming soon") : badge("Available")}
        </div>

        <div className="mt-4">
          <h3 className="text-sm font-extrabold uppercase tracking-[0.18em] text-white">{props.title}</h3>
          <p className="mt-2 text-[12px] leading-relaxed text-gray-400">{props.subtitle}</p>
        </div>

        <ul className="mt-4 space-y-2 text-[13px] leading-relaxed text-gray-300">
          {props.items.map((it, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className={["mt-2 h-1 w-1 rounded-full", cls.glowBg].join(" ")} />
              <span className="text-gray-400">{it}</span>
            </li>
          ))}
        </ul>

        <button
          className="mt-6 inline-flex w-full items-center justify-between rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-[11px] uppercase tracking-widest text-gray-300 hover:bg-white/10 transition-colors"
          type="button"
        >
          <span>Learn more</span>
          <ChevronRight className="h-4 w-4 text-gray-400" />
        </button>
      </div>
    </div>
  );
}

function RepoImportPanel(props: {
  repoUrl: string;
  setRepoUrl: (v: string) => void;
  onRun: () => void;
  running: boolean;
  error: string | null;
}) {
  const canRun = props.repoUrl.trim().startsWith("https://github.com/") && !props.running;

  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-md p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-sm font-extrabold uppercase tracking-[0.18em] text-white">Import a GitHub repo</h3>
          <p className="mt-2 text-[13px] leading-relaxed text-gray-400">
            Paste a public GitHub repository URL. dpylens will clone + analyze it and embed the report below.
          </p>
        </div>
        {badge("Local dev")}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto]">
        <input
          className="w-full rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-sm text-gray-200 placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/30"
          placeholder="https://github.com/owner/repo"
          value={props.repoUrl}
          onChange={(e) => props.setRepoUrl(e.target.value)}
        />
        <button
          className={[
            "rounded-xl px-5 py-3 text-sm font-semibold border",
            canRun
              ? "bg-cyan-500/20 text-cyan-200 border-cyan-500/30 hover:bg-cyan-500/25"
              : "cursor-not-allowed bg-white/5 text-gray-500 border-white/10"
          ].join(" ")}
          disabled={!canRun}
          onClick={props.onRun}
          type="button"
        >
          {props.running ? "Running..." : "Run Analysis"}
        </button>
      </div>

      {props.error ? (
        <div className="mt-3 rounded-xl border border-red-500/20 bg-red-500/10 p-3 text-[12px] text-red-200">
          {props.error}
        </div>
      ) : (
        <div className="mt-3 text-[12px] text-gray-500">
          API: <code className="text-gray-300">http://localhost:8787</code>
        </div>
      )}
    </div>
  );
}

function ExecutionTraceWidget(props: { status: string; lastRun?: AnalyzeResponse | null }) {
  return (
    <div className="fixed bottom-6 right-6 hidden w-[360px] rounded-xl border border-white/10 bg-black/60 p-4 shadow-2xl backdrop-blur-xl xl:block">
      <div className="flex items-center gap-2 border-b border-white/10 pb-2">
        <Terminal className="h-4 w-4 text-emerald-400" />
        <span className="font-mono text-[10px] font-bold uppercase tracking-[0.18em] text-gray-400">
          Execution Trace
        </span>
        <span className="ml-auto inline-flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_20px_rgba(52,211,153,0.35)]" />
      </div>

      <div className="mt-3 space-y-1 font-mono text-[11px] text-gray-400">
        <div className="text-emerald-300/80">&gt; POST /analyze</div>
        <div>Status: {props.status}</div>
        {props.lastRun ? (
          <>
            <div className="text-cyan-300/80">Files: {props.lastRun.files_analyzed}</div>
            <div className="text-gray-500">Parse errors: {props.lastRun.parse_errors}</div>
            <div className="text-gray-500">Run ID: {props.lastRun.run_id}</div>
          </>
        ) : (
          <div className="text-gray-500">Idle — waiting for repo URL.</div>
        )}
      </div>
    </div>
  );
}

export function LandingPage() {
  const [repoUrl, setRepoUrl] = useState("https://github.com/malkiats/test-lapwing");
  const [running, setRunning] = useState(false);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const features: Feature[] = useMemo(
    () => [
      {
        title: "Code Analyzer",
        subtitle: "AST parsing, dependency mapping, call resolution.",
        color: "blue",
        icon: Code2,
        ready: true,
        items: ["AST parsing", "Dependency mapping", "Call graph + resolution", "Patterns & heuristics"]
      },
      {
        title: "Visualizer",
        subtitle: "Graphs + report explorer for modules and calls.",
        color: "cyan",
        icon: Share2,
        ready: true,
        items: ["Module graph (DAG)", "Call graph overview", "Dataflow mapping", "Report export"]
      },
      {
        title: "Test Generator",
        subtitle: "Pytest and mocking suggestions (planned).",
        color: "orange",
        icon: FlaskConical,
        ready: false,
        items: ["Pytest scaffolds", "Mocking suggestions", "Edge-case coverage", "Coverage gap surfacing"]
      },
      {
        title: "AI Comprehension",
        subtitle: "Auto-doc and architecture maps (planned).",
        color: "teal",
        icon: BrainCircuit,
        ready: false,
        items: ["Auto-doc summaries", "Architecture maps", "Q&A on code intent", "Anti-pattern detection"]
      },
      {
        title: "IaC Validator",
        subtitle: "Pulumi/CDK validation & cost estimation (planned).",
        color: "indigo",
        icon: ShieldCheck,
        ready: false,
        items: ["Pulumi/CDK checks", "Policy validation", "Cost estimation", "Security posture hints"]
      },
      {
        title: "Runtime Monitoring",
        subtitle: "Trace capture & error playback (planned).",
        color: "amber",
        icon: Activity,
        ready: false,
        items: ["Trace capture", "Replay timelines", "Error playback", "Team collaboration"]
      }
    ],
    []
  );

  async function onRun() {
    setError(null);
    setRunning(true);
    setStatus("cloning → analyzing → rendering → report");

    try {
      const r = await analyzeRepo({ repo_url: repoUrl, render: true });
      setResult(r);
      setStatus("complete");
    } catch (e) {
      setError(String(e));
      setStatus("failed");
    } finally {
      setRunning(false);
    }
  }

  const bg = circuitDataUri();

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-200">
      <div
        className="pointer-events-none fixed inset-0 opacity-[0.055]"
        style={{ backgroundImage: `url("${bg}")`, backgroundSize: "720px 720px" }}
      />
      <div className="pointer-events-none fixed inset-x-0 top-0 h-[480px] bg-[radial-gradient(ellipse_at_top,rgba(34,211,238,0.10),rgba(0,0,0,0))]" />

      <div className="relative mx-auto max-w-7xl px-6 pb-20 pt-12">
        <header className="text-center">
          <div className="mx-auto inline-flex items-center justify-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-teal-400 shadow-lg shadow-blue-500/20">
              <span className="select-none text-lg font-black italic text-black">py</span>
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-white">dpylens</h1>
          </div>

          <p className="mt-4 text-lg font-semibold text-transparent bg-clip-text bg-gradient-to-r from-gray-100 to-gray-500">
            DevOps Python Intelligence Platform
          </p>

          <p className="mx-auto mt-3 max-w-3xl text-sm leading-relaxed text-gray-400">
            Import a repo, run static analysis, generate a deterministic summary, and view the dpylens report.
          </p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            {badge("Dark Intelligence UI")}
            {badge("Static Analysis")}
            {badge("Embedded Report")}
            {badge("Heuristic Summary (No LLM)")}
          </div>
        </header>

        <div className="mt-10">
          <RepoImportPanel repoUrl={repoUrl} setRepoUrl={setRepoUrl} onRun={onRun} running={running} error={error} />
        </div>

        <main className="mt-10">
          <h2 className="text-sm font-extrabold uppercase tracking-[0.18em] text-white">Capability Modules</h2>
          <p className="mt-2 text-[13px] text-gray-400">
            Analyzer/Visualizer are ready. Other modules are staged (Coming Soon).
          </p>

          <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            {features.map((f) => (
              <FeatureCard key={f.title} {...f} />
            ))}
          </div>
        </main>

        {/* SUMMARY + REPORT */}
        <section className="mt-12">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-extrabold uppercase tracking-[0.18em] text-white">Repo Summary</h2>

            {result ? (
              <div className="flex flex-wrap gap-2">
                <a
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[12px] text-gray-300 hover:bg-white/10"
                  href={downloadUrlAbsolute(result.download_report_url)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download report.zip
                </a>
                <a
                  className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-[12px] text-gray-300 hover:bg-white/10"
                  href={downloadUrlAbsolute(result.download_analysis_zip_url)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download analysis.zip
                </a>
              </div>
            ) : null}
          </div>

          <p className="mt-2 text-[13px] text-gray-400">
            Summary is generated from dpylens outputs (imports, module graph, call graph, patterns, dataflow).
          </p>

          <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
            {result ? (
              <div className="p-6">
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <pre className="whitespace-pre-wrap text-[13px] leading-relaxed text-gray-200">
                    {result.description_markdown}
                  </pre>
                </div>

                <h2 className="mt-10 text-sm font-extrabold uppercase tracking-[0.18em] text-white">Report</h2>
                <p className="mt-2 text-[13px] text-gray-400">Embedded HTML report generated by dpylens.</p>

                <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-white/[0.03]">
                  <iframe title="dpylens report" className="h-[820px] w-full" src={reportUrlAbsolute(result.report_url)} />
                </div>
              </div>
            ) : (
              <div className="p-6 text-[13px] text-gray-500">
                No analysis yet. Paste a GitHub URL and click <span className="text-gray-300">Run Analysis</span>.
              </div>
            )}
          </div>
        </section>

        <footer className="mt-14 border-t border-white/10 pt-6 text-center text-[12px] text-gray-500">
          <div>dpylens — static intelligence for Python + DevOps workflows.</div>
        </footer>
      </div>

      <ExecutionTraceWidget status={status} lastRun={result} />
    </div>
  );
}