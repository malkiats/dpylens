from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.aliases import extract_alias_maps
from dpylens.analyzer.callgraph import extract_callgraph
from dpylens.analyzer.callgraph_resolve import resolve_calls
from dpylens.analyzer.models import FunctionRecord
from dpylens.analyzer.modulegraph import build_local_module_index, module_name_for_file


def test_call_resolution_from_relative_import(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pkg = root / "dpylens" / "analyzer"
    pkg.mkdir(parents=True)

    parser_path = pkg / "parser.py"
    parser_path.write_text(
        "def parse_file_to_ast(x):\n"
        "    return x\n",
        encoding="utf-8",
    )

    cli_path = pkg / "cli.py"
    cli_path.write_text(
        "from .parser import parse_file_to_ast\n"
        "def main():\n"
        "    parse_file_to_ast('x')\n",
        encoding="utf-8",
    )

    # Build local index so resolve_calls signature is satisfied
    py_files = [parser_path, cli_path]
    local_index = build_local_module_index(root, py_files)

    # Parse + extract functions/calls from cli.py
    tree_cli = ast.parse(cli_path.read_text(encoding="utf-8"), filename=str(cli_path))
    mod_cli = module_name_for_file(root, cli_path)
    funcs_cli, calls_cli = extract_callgraph(tree_cli, cli_path, module_name=mod_cli)

    # Also include the parser function in "known functions" set
    parser_func = FunctionRecord(
        qualname=f"{module_name_for_file(root, parser_path)}.parse_file_to_ast",
        file=str(parser_path),
        lineno=1,
    )
    all_functions = funcs_cli + [parser_func]

    aliases_cli = extract_alias_maps(tree_cli, cli_path, root=root)
    resolved = resolve_calls(
        functions=all_functions,
        calls=calls_cli,
        alias_maps_by_file={str(cli_path): aliases_cli},
        local_module_index=local_index,
    )

    assert len(resolved) == 1
    assert resolved[0].callee_raw == "parse_file_to_ast"
    assert resolved[0].callee_resolved == "dpylens.analyzer.parser.parse_file_to_ast"


def test_call_resolution_module_alias(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pkg = root / "dpylens" / "analyzer"
    pkg.mkdir(parents=True)

    parser_path = pkg / "parser.py"
    parser_path.write_text(
        "def parse_file_to_ast(x):\n"
        "    return x\n",
        encoding="utf-8",
    )

    cli_path = pkg / "cli.py"
    cli_path.write_text(
        "import dpylens.analyzer.parser as p\n"
        "def main():\n"
        "    p.parse_file_to_ast('x')\n",
        encoding="utf-8",
    )

    py_files = [parser_path, cli_path]
    local_index = build_local_module_index(root, py_files)

    tree_cli = ast.parse(cli_path.read_text(encoding="utf-8"), filename=str(cli_path))
    mod_cli = module_name_for_file(root, cli_path)
    funcs_cli, calls_cli = extract_callgraph(tree_cli, cli_path, module_name=mod_cli)

    parser_func = FunctionRecord(
        qualname=f"{module_name_for_file(root, parser_path)}.parse_file_to_ast",
        file=str(parser_path),
        lineno=1,
    )
    all_functions = funcs_cli + [parser_func]

    aliases_cli = extract_alias_maps(tree_cli, cli_path, root=root)
    resolved = resolve_calls(
        functions=all_functions,
        calls=calls_cli,
        alias_maps_by_file={str(cli_path): aliases_cli},
        local_module_index=local_index,
    )

    assert len(resolved) == 1
    assert resolved[0].callee_raw == "p.parse_file_to_ast"
    assert resolved[0].callee_resolved == "dpylens.analyzer.parser.parse_file_to_ast"