from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RenderResult:
    rendered: list[str]
    skipped: list[str]
    warnings: list[str]


DOT_TO_PNG = [
    ("imports.dot", "imports.png"),
    ("module_graph.dot", "module_graph.png"),
    ("callgraph.dot", "callgraph.png"),
    ("callgraph_grouped.dot", "callgraph_grouped.png"),
    ("dataflow.dot", "dataflow.png"),
]


def find_dot() -> str | None:
    return shutil.which("dot")


def render_dot_to_png(analysis_dir: Path) -> RenderResult:
    rendered: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []

    dot = find_dot()
    if not dot:
        warnings.append("Graphviz 'dot' not found on PATH. Skipping PNG rendering.")
        return RenderResult(rendered=rendered, skipped=[src for src, _ in DOT_TO_PNG], warnings=warnings)

    for src_name, out_name in DOT_TO_PNG:
        src = analysis_dir / src_name
        out = analysis_dir / out_name
        if not src.exists():
            skipped.append(src_name)
            continue

        try:
            subprocess.run([dot, "-Tpng", str(src), "-o", str(out)], check=True, capture_output=True, text=True)
            rendered.append(out_name)
        except subprocess.CalledProcessError as e:
            warnings.append(f"Failed rendering {src_name}: {e.stderr.strip() or e.stdout.strip() or 'unknown error'}")

    return RenderResult(rendered=rendered, skipped=skipped, warnings=warnings)