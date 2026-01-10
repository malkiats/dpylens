from __future__ import annotations

import argparse
import json
from pathlib import Path

from dpylens.analyzer.callgraph import extract_callgraph
from dpylens.analyzer.imports import extract_imports
from dpylens.analyzer.models import FileError, to_jsonable
from dpylens.analyzer.parser import parse_file_to_ast
from dpylens.analyzer.scanner import scan_python_files
from dpylens.analyzer.visualize import (
    build_callgraph_dot,
    build_callgraph_grouped_dot,
    build_imports_dot,
    write_text,
)


def _module_name_from_path(root: Path, file_path: Path) -> str:
    """
    Convert a path to a module-like name for display:
      root/src/app/utils.py -> src.app.utils
    """
    rel = file_path.resolve().relative_to(root.resolve())
    no_suffix = rel.with_suffix("")
    return ".".join(no_suffix.parts)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def cmd_analyze(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    out = Path(args.out).resolve()

    py_files = scan_python_files(root)
    errors: list[FileError] = []

    import_records = []
    all_functions = []
    all_calls = []

    for f in py_files:
        tree, err = parse_file_to_ast(f)
        if err:
            errors.append(err)
            continue
        assert tree is not None

        import_records.append(extract_imports(tree, f))

        module_name = _module_name_from_path(root, f)
        funcs, calls = extract_callgraph(tree, f, module_name=module_name)
        all_functions.extend(funcs)
        all_calls.extend(calls)

    # JSON outputs
    write_json(out / "modules.json", {"imports": to_jsonable(import_records), "errors": to_jsonable(errors)})
    write_json(
        out / "callgraph.json",
        {"functions": to_jsonable(all_functions), "calls": to_jsonable(all_calls), "errors": to_jsonable(errors)},
    )

    # DOT outputs (visualization)
    write_text(out / "imports.dot", build_imports_dot(import_records))
    write_text(out / "callgraph.dot", build_callgraph_dot(all_calls))
    write_text(out / "callgraph_grouped.dot", build_callgraph_grouped_dot(all_calls))

    print(f"Analyzed {len(py_files)} Python files.")
    print(f"Wrote JSON + DOT outputs to: {out}")
    if errors:
        print(f"Warnings: {len(errors)} files failed to parse. See JSON output for details.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dpylens", description="DevOps Python Intelligence Platform (MVP Analyzer)")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyze", help="Analyze a folder of Python files and output JSON/DOT artifacts")
    a.add_argument("path", help="Root folder to analyze (e.g. .)")
    a.add_argument("--out", default="analysis", help="Output folder for analysis artifacts (default: analysis)")
    a.set_defaults(func=cmd_analyze)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))