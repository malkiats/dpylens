from __future__ import annotations

from pathlib import Path

from dpylens.analyzer.imports import ImportRecord
from dpylens.analyzer.models import CallRecord


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _dot_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_imports_dot(imports: list[ImportRecord]) -> str:
    """
    DOT graph:
      file -> imported_module (flattened base modules)
    """
    lines = [
        "digraph imports {",
        '  rankdir="LR";',
        '  node [shape="box", fontsize=10];',
    ]
    for rec in imports:
        f = _dot_escape(rec.file)
        for imp in rec.imports:
            m = _dot_escape(imp)
            lines.append(f'  "{f}" -> "{m}";')
    lines.append("}")
    return "\n".join(lines)


def build_callgraph_dot(calls: list[CallRecord]) -> str:
    lines = [
        "digraph callgraph {",
        '  rankdir="LR";',
        '  node [shape="ellipse", fontsize=10];',
    ]
    for c in calls:
        caller = _dot_escape(c.caller)
        callee = _dot_escape(c.callee)
        lines.append(f'  "{caller}" -> "{callee}";')
    lines.append("}")
    return "\n".join(lines)


def build_callgraph_grouped_dot(calls: list[CallRecord]) -> str:
    from collections import defaultdict

    by_file: dict[str, list[CallRecord]] = defaultdict(list)
    for c in calls:
        by_file[c.file].append(c)

    lines = [
        "digraph callgraph_grouped {",
        '  rankdir="LR";',
        '  node [shape="ellipse", fontsize=10];',
    ]

    for idx, (file, edges) in enumerate(sorted(by_file.items(), key=lambda x: x[0])):
        file_esc = _dot_escape(file)
        lines.append(f'  subgraph cluster_{idx} {{')
        lines.append(f'    label="{file_esc}";')
        lines.append('    style="rounded";')
        for c in edges:
            caller = _dot_escape(c.caller)
            callee = _dot_escape(c.callee)
            lines.append(f'    "{caller}" -> "{callee}";')
        lines.append("  }")

    lines.append("}")
    return "\n".join(lines)