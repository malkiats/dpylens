from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from git import Repo
from pydantic import BaseModel, HttpUrl

from dpylens.cli import analyze_project
from dpylens.rendering.graphviz import render_dot_to_png
from dpylens.reporter.html_report import ReportPaths, build_report

from api.summary_builder import build_repo_summary, build_description_markdown

APP_DATA_DIR = Path(".dpylens-server").resolve()
RUNS_DIR = APP_DATA_DIR / "runs"


class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    render: bool = True


class AnalyzeResponse(BaseModel):
    run_id: str
    repo_url: str
    analysis_dir: str
    report_dir: str
    warnings: list[str]
    files_analyzed: int
    parse_errors: int

    report_url: str

    summary: dict[str, Any]
    description_markdown: str

    download_report_url: str
    download_analysis_zip_url: str


app = FastAPI(title="dpylens api", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)


def _zip_dir(src_dir: Path, out_zip: Path) -> Path:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    base_name = str(out_zip).removesuffix(".zip")
    shutil.make_archive(base_name, "zip", root_dir=str(src_dir))
    return Path(base_name + ".zip")


def _run_dir(run_id: str) -> Path:
    return RUNS_DIR / run_id


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest) -> AnalyzeResponse:
    _ensure_dirs()

    run_id = uuid.uuid4().hex[:12]
    run_dir = RUNS_DIR / run_id
    repo_dir = run_dir / "repo"
    analysis_dir = run_dir / "analysis"
    report_dir = run_dir / "report"

    warnings: list[str] = []

    try:
        run_dir.mkdir(parents=True, exist_ok=True)

        # Clone repo (shallow)
        Repo.clone_from(str(req.repo_url), str(repo_dir), depth=1)

        # Analyze
        files_analyzed, errors = analyze_project(root=repo_dir, out=analysis_dir)

        # Optional render
        if req.render:
            rr = render_dot_to_png(analysis_dir)
            warnings.extend(rr.warnings)

        # Report
        build_report(ReportPaths(analysis_dir=analysis_dir, report_dir=report_dir))

        # Heuristic summary + description
        summary = build_repo_summary(analysis_dir)
        description = build_description_markdown(str(req.repo_url), summary)

        # Downloads
        _zip_dir(report_dir, run_dir / "report.zip")
        _zip_dir(analysis_dir, run_dir / "analysis.zip")

        return AnalyzeResponse(
            run_id=run_id,
            repo_url=str(req.repo_url),
            analysis_dir=str(analysis_dir),
            report_dir=str(report_dir),
            warnings=warnings,
            files_analyzed=files_analyzed,
            parse_errors=len(errors),
            report_url=f"/runs/{run_id}/report/",
            summary=summary,
            description_markdown=description,
            download_report_url=f"/runs/{run_id}/report.zip",
            download_analysis_zip_url=f"/runs/{run_id}/analysis.zip",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analyze failed: {e}") from e


@app.get("/runs/{run_id}/report/")
def report_index(run_id: str) -> Any:
    p = _run_dir(run_id) / "report" / "index.html"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(p), media_type="text/html; charset=utf-8")


@app.get("/runs/{run_id}/report/{asset_path:path}")
def report_asset(run_id: str, asset_path: str) -> Any:
    base = (_run_dir(run_id) / "report").resolve()
    target = (base / asset_path).resolve()

    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Invalid path")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(str(target))


@app.get("/runs/{run_id}/report.zip")
def download_report(run_id: str) -> Any:
    p = _run_dir(run_id) / "report.zip"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(p), filename=f"dpylens-report-{run_id}.zip")


@app.get("/runs/{run_id}/analysis.zip")
def download_analysis(run_id: str) -> Any:
    p = _run_dir(run_id) / "analysis.zip"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(p), filename=f"dpylens-analysis-{run_id}.zip")