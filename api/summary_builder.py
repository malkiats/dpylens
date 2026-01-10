from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def build_repo_summary(analysis_dir: Path, max_items: int = 20) -> dict[str, Any]:
    modules = _read_json(analysis_dir / "modules.json")
    module_graph = _read_json(analysis_dir / "module_graph.json")
    callgraph = _read_json(analysis_dir / "callgraph.json")
    patterns = _read_json(analysis_dir / "patterns.json")
    dataflow = _read_json(analysis_dir / "dataflow.json")

    resolved = None
    resolved_path = analysis_dir / "callgraph_resolved.json"
    if resolved_path.exists():
        resolved = _read_json(resolved_path)

    imports = modules.get("imports", []) or []
    files = [r.get("file") for r in imports if r.get("file")]

    imported_modules = Counter()
    for r in imports:
        for it in r.get("items", []) or []:
            m = (it.get("module") or "").strip()
            if m:
                imported_modules[m] += 1

    edges = module_graph.get("edges", []) or []
    out_deg = Counter()
    in_deg = Counter()
    for e in edges:
        s = e.get("src")
        t = e.get("dst")
        if s:
            out_deg[s] += 1
        if t:
            in_deg[t] += 1

    calls = (resolved or callgraph).get("calls", []) or []
    calls_by_caller = defaultdict(int)
    unique_callees = defaultdict(set)
    calls_by_file = Counter()

    for c in calls:
        caller = c.get("caller") or ""
        callee = c.get("callee_resolved") or c.get("callee_raw") or c.get("callee") or ""
        f = c.get("file") or ""
        if f:
            calls_by_file[f] += 1
        if caller and callee:
            calls_by_caller[caller] += 1
            unique_callees[caller].add(callee)

    top_callers = sorted(calls_by_caller.items(), key=lambda x: x[1], reverse=True)[:max_items]
    top_fanout = sorted(((k, len(v)) for k, v in unique_callees.items()), key=lambda x: x[1], reverse=True)[:max_items]
    top_call_files = calls_by_file.most_common(max_items)

    pattern_hits = patterns.get("patterns", []) or []
    pattern_counts = Counter()
    files_with_patterns = 0
    for p in pattern_hits:
        pats = p.get("patterns") or []
        if pats:
            files_with_patterns += 1
        for pat in pats:
            pattern_counts[pat] += 1

    df_fns = dataflow.get("functions", []) or []
    df_inputs = Counter()
    df_outputs = Counter()
    for f in df_fns:
        for i in f.get("inputs") or []:
            df_inputs[str(i)] += 1
        for o in f.get("outputs") or []:
            df_outputs[str(o)] += 1

    errors_total = (
        len(modules.get("errors", []) or [])
        + len(module_graph.get("errors", []) or [])
        + len(callgraph.get("errors", []) or [])
        + len(patterns.get("errors", []) or [])
        + len(dataflow.get("errors", []) or [])
    )

    return {
        "counts": {
            "files": len(files),
            "module_edges": len(edges),
            "functions": len(callgraph.get("functions", []) or []),
            "calls": len(callgraph.get("calls", []) or []),
            "resolved_calls": len((resolved or {}).get("calls", []) or []) if resolved else 0,
            "dataflow_functions": len(df_fns),
            "files_with_patterns": files_with_patterns,
            "warnings": errors_total,
        },
        "top_imported_modules": [{"module": m, "count": c} for m, c in imported_modules.most_common(max_items)],
        "module_graph": {
            "top_out_degree": [{"module": m, "out": c} for m, c in out_deg.most_common(max_items)],
            "top_in_degree": [{"module": m, "in": c} for m, c in in_deg.most_common(max_items)],
        },
        "call_graph": {
            "top_callers_by_calls": [{"caller": k, "calls": v} for k, v in top_callers],
            "top_fanout_callers": [{"caller": k, "unique_callees": v} for k, v in top_fanout],
            "top_call_files": [{"file": f, "calls": c} for f, c in top_call_files],
        },
        "patterns": [{"pattern": p, "count": c} for p, c in pattern_counts.most_common(max_items)],
        "dataflow": {
            "top_inputs": [{"input": k, "count": v} for k, v in df_inputs.most_common(15)],
            "top_outputs": [{"output": k, "count": v} for k, v in df_outputs.most_common(15)],
        },
    }


def build_description_markdown(repo_url: str, summary: dict[str, Any]) -> str:
    c = summary.get("counts", {})

    top_imports = summary.get("top_imported_modules", [])[:10]
    top_out = (summary.get("module_graph", {}) or {}).get("top_out_degree", [])[:10]
    top_in = (summary.get("module_graph", {}) or {}).get("top_in_degree", [])[:10]

    cg = summary.get("call_graph", {}) or {}
    top_callers = cg.get("top_callers_by_calls", [])[:10]
    top_fanout = cg.get("top_fanout_callers", [])[:10]
    top_call_files = cg.get("top_call_files", [])[:8]

    pats = summary.get("patterns", [])[:12]
    df = summary.get("dataflow", {}) or {}
    df_in = df.get("top_inputs", [])[:10]
    df_out = df.get("top_outputs", [])[:10]

    def fmt_kv(items: list[dict[str, Any]], k1: str, k2: str) -> str:
        if not items:
            return "_No data._"
        return "\n".join([f"- `{it.get(k1)}` — **{it.get(k2)}**" for it in items])

    md: list[str] = []
    md.append("# Repository Summary")
    md.append(f"**Repo:** {repo_url}")
    md.append("")
    md.append("## What dpylens observed (high level)")
    md.append(f"- Files analyzed: **{c.get('files', 0)}**")
    md.append(f"- Functions found: **{c.get('functions', 0)}**")
    md.append(f"- Calls found: **{c.get('calls', 0)}** (resolved: **{c.get('resolved_calls', 0)}**)")
    md.append(f"- Module edges: **{c.get('module_edges', 0)}**")
    md.append(f"- Dataflow functions: **{c.get('dataflow_functions', 0)}**")
    md.append(f"- Pattern hits: **{c.get('files_with_patterns', 0)}** files")
    md.append(f"- Warnings: **{c.get('warnings', 0)}**")
    md.append("")
    md.append("## Likely responsibilities / ecosystem")
    md.append("Top imported modules (signals dependencies and domain):")
    md.append(fmt_kv(top_imports, "module", "count"))
    md.append("")
    md.append("## Architecture signals (module graph)")
    md.append("High out-degree modules (depend on many others):")
    md.append(fmt_kv(top_out, "module", "out"))
    md.append("")
    md.append("High in-degree modules (used by many others):")
    md.append(fmt_kv(top_in, "module", "in"))
    md.append("")
    md.append("## Execution signals (call graph)")
    md.append("Top callers by number of calls:")
    md.append(fmt_kv(top_callers, "caller", "calls"))
    md.append("")
    md.append("Top callers by unique callees (fan-out):")
    md.append(fmt_kv(top_fanout, "caller", "unique_callees"))
    md.append("")
    md.append("Files with most calls recorded:")
    md.append(fmt_kv(top_call_files, "file", "calls"))
    md.append("")
    md.append("## Patterns & heuristics")
    md.append(fmt_kv(pats, "pattern", "count"))
    md.append("")
    md.append("## Dataflow hints (heuristic)")
    md.append("Top inputs:")
    md.append(fmt_kv(df_in, "input", "count"))
    md.append("")
    md.append("Top outputs:")
    md.append(fmt_kv(df_out, "output", "count"))
    md.append("")
    md.append("## Notes / limitations")
    md.append("- This description is generated **without an LLM**, purely from dpylens static-analysis outputs.")
    md.append("- Exact runtime behavior may differ (dynamic imports, reflection, external config).")
    md.append("- Use the embedded report to inspect graphs and per-file/per-function details.")
    md.append("")
    return "\n".join(md)