export type AnalyzeRequest = {
  repo_url: string;
  render?: boolean;
};

export type AnalyzeResponse = {
  run_id: string;
  repo_url: string;
  warnings: string[];
  files_analyzed: number;
  parse_errors: number;

  report_url: string;

  summary: unknown;
  description_markdown: string;

  download_report_url: string;
  download_analysis_zip_url: string;
};

const API_BASE = "http://localhost:8787";

export async function analyzeRepo(req: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ render: true, ...req })
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }

  return (await res.json()) as AnalyzeResponse;
}

export function reportUrlAbsolute(report_url: string): string {
  return `${API_BASE}${report_url}`;
}

export function downloadUrlAbsolute(path: string): string {
  return `${API_BASE}${path}`;
}