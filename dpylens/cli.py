from __future__ import annotations

import argparse
import json
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from dpylens.analyzer.aliases import extract_alias_maps
from dpylens.analyzer.callgraph import extract_callgraph
from dpylens.analyzer.callgraph_resolve import resolve_calls
from dpylens.analyzer.dataflow import extract_dataflow
from dpylens.analyzer.imports import extract_imports
from dpylens.analyzer.layout import detect_package_layout, module_name_for_file_with_layout
from dpylens.analyzer.models import FileError, to_jsonable
from dpylens.analyzer.modulegraph import build_module_graph, build_local_module_index
from dpylens.analyzer.parser import parse_file_to_ast
from dpylens.analyzer.patterns import detect_patterns
from dpylens.analyzer.routes_litestar import analyze_litestar_routes
from dpylens.analyzer.scanner import scan_python_files
from dpylens.analyzer.visualize import (
    build_callgraph_dot,
    build_callgraph_grouped_dot,
    build_imports_dot,
    write_text,
)
from dpylens.analyzer.visualize_dataflow import build_dataflow_dot
from dpylens.analyzer.visualize_modulegraph import build_module_graph_dot
from dpylens.rendering.graphviz import render_dot_to_png
from dpylens.reporter.html_report import ReportPaths, build_report


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def analyze_project(root: Path, out: Path) -> tuple[int, list[FileError]]:
    out.mkdir(parents=True, exist_ok=True)

    py_files = scan_python_files(root)
    errors: list[FileError] = []

    layout = detect_package_layout(root)

    import_records = []
    all_functions = []
    all_calls = []

    pattern_hits = []
    all_dataflows = []

    alias_maps_by_file = {}

    for f in py_files:
        tree, err = parse_file_to_ast(f)
        if err:
            errors.append(err)
            continue
        assert tree is not None

        imp_rec = extract_imports(tree, f)
        import_records.append(imp_rec)

        module_name = module_name_for_file_with_layout(layout, f)

        alias_maps_by_file[str(f)] = extract_alias_maps(tree, f, root=root)

        funcs, calls = extract_callgraph(tree, f, module_name=module_name)
        all_functions.extend(funcs)
        all_calls.extend(calls)

        pattern_hits.append(detect_patterns(tree, imp_rec, f))
        all_dataflows.extend(extract_dataflow(tree, f, module_name=module_name))

    mod_nodes, mod_edges = build_module_graph(root=root, py_files=py_files, import_records=import_records)
    local_module_index = build_local_module_index(root, py_files)

    resolved_calls = resolve_calls(
        functions=all_functions,
        calls=all_calls,
        alias_maps_by_file=alias_maps_by_file,
        local_module_index=local_module_index,
    )

    # --- NEW: routes extraction (best-effort; must not break analysis) ---
    try:
        rr = analyze_litestar_routes(root=root, out_dir=out)
        # store warnings in a JSON file as well (routes.json already includes warnings)
        # also record them in "errors" list in a non-fatal way
        for w in rr.warnings:
            errors.append(FileError(file="routes_litestar", error=w))
    except Exception as e:  # noqa: BLE001
        errors.append(FileError(file="routes_litestar", error=f"routes_analyzer_failed: {e}"))

    # JSON
    write_json(out / "modules.json", {"imports": to_jsonable(import_records), "errors": to_jsonable(errors)})
    write_json(
        out / "module_graph.json",
        {"nodes": to_jsonable(mod_nodes), "edges": to_jsonable(mod_edges), "errors": to_jsonable(errors)},
    )
    write_json(
        out / "callgraph.json",
        {"functions": to_jsonable(all_functions), "calls": to_jsonable(all_calls), "errors": to_jsonable(errors)},
    )
    write_json(
        out / "callgraph_resolved.json",
        {"functions": to_jsonable(all_functions), "calls": to_jsonable(resolved_calls), "errors": to_jsonable(errors)},
    )
    write_json(out / "patterns.json", {"patterns": to_jsonable(pattern_hits), "errors": to_jsonable(errors)})
    write_json(out / "dataflow.json", {"functions": to_jsonable(all_dataflows), "errors": to_jsonable(errors)})

    # DOT
    write_text(out / "imports.dot", build_imports_dot(import_records))
    write_text(out / "module_graph.dot", build_module_graph_dot(mod_nodes, mod_edges))
    write_text(out / "callgraph.dot", build_callgraph_dot(all_calls))
    write_text(out / "callgraph_grouped.dot", build_callgraph_grouped_dot(all_calls))
    write_text(out / "dataflow.dot", build_dataflow_dot(all_dataflows))

    return len(py_files), errors


def cmd_analyze(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    out = Path(args.out).resolve()

    nfiles, errors = analyze_project(root=root, out=out)

    print(f"Analyzed {nfiles} Python files.")
    print(f"Wrote JSON + DOT outputs to: {out}")
    if errors:
        print(f"Warnings: {len(errors)} issues (parse or analysis). See JSON output for details.")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis).resolve()
    report_dir = Path(args.out).resolve()

    build_report(ReportPaths(analysis_dir=analysis_dir, report_dir=report_dir))

    print(f"Wrote report to: {report_dir}")
    print("To view:")
    print(f"  cd {report_dir}")
    print("  python -m http.server")
    print("  open http://localhost:8000")
    return 0


def _serve_report(report_dir: Path, port: int) -> ThreadingHTTPServer:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(report_dir), **kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def cmd_run(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    analysis_out = Path(args.analysis_out).resolve()
    report_out = Path(args.report_out).resolve()

    nfiles, errors = analyze_project(root=root, out=analysis_out)

    if args.render:
        res = render_dot_to_png(analysis_out)
        for w in res.warnings:
            print(f"Warning: {w}")
        if res.rendered:
            print(f"Rendered PNGs: {', '.join(res.rendered)}")
        else:
            print("Rendered PNGs: none")

    build_report(ReportPaths(analysis_dir=analysis_out, report_dir=report_out))

    print(f"Analyzed {nfiles} Python files.")
    print(f"Analysis: {analysis_out}")
    print(f"Report: {report_out}")
    if errors:
        print(f"Warnings: {len(errors)} issues (parse or analysis). See analysis JSON output for details.")

    if args.serve:
        port = int(args.port)
        server = _serve_report(report_out, port=port)
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        print(f"Serving report at: {url}")
        if args.open:
            webbrowser.open(url)

        if not args.no_wait:
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                server.shutdown()
        return 0

    print("To view report:")
    print(f"  cd {report_out}")
    print("  python -m http.server")
    print("  open http://localhost:8000")
    if args.open:
        webbrowser.open((report_out / "index.html").as_uri())

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dpylens", description="DevOps Python Intelligence Platform (MVP Analyzer)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Analyze a folder of Python files and output JSON/DOT artifacts")
    a.add_argument("path", help="Root folder to analyze (e.g. .)")
    a.add_argument("--out", default="analysis", help="Output folder for analysis artifacts (default: analysis)")
    a.set_defaults(func=cmd_analyze)

    r = sub.add_parser("report", help="Generate a static HTML report from analysis outputs")
    r.add_argument("--analysis", default="analysis", help="Folder containing analysis JSON outputs (default: analysis)")
    r.add_argument("--out", default="report", help="Output folder for report (default: report)")
    r.set_defaults(func=cmd_report)

    run = sub.add_parser("run", help="Run analyze (+optional PNG render) then generate report")
    run.add_argument("path", help="Root folder to analyze (e.g. .)")
    run.add_argument("--analysis-out", default="analysis", help="Output folder for analysis artifacts (default: analysis)")
    run.add_argument("--report-out", default="report", help="Output folder for report artifacts (default: report)")
    run.add_argument("--render", action="store_true", help="If Graphviz 'dot' is available, render PNGs from DOT")
    run.add_argument("--open", action="store_true", help="Open the report in your browser")
    run.add_argument("--serve", action="store_true", help="Serve report via an embedded HTTP server (recommended with --open)")
    run.add_argument("--port", default="8000", help="Port for --serve (default: 8000)")
    run.add_argument(
        "--no-wait",
        action="store_true",
        help="With --serve, do not block; start server and exit (not recommended: server will die when process exits)",
    )
    run.set_defaults(func=cmd_run)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))