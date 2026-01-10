from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.aliases import extract_alias_maps


def test_extract_alias_maps_resolves_relative_from_import(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pkg = root / "dpylens" / "analyzer"
    pkg.mkdir(parents=True)

    # file where the relative import exists
    cli_path = pkg / "cli.py"
    cli_path.write_text(
        "from .parser import parse_file_to_ast\n"
        "def main():\n"
        "    parse_file_to_ast('x')\n",
        encoding="utf-8",
    )

    tree = ast.parse(cli_path.read_text(encoding="utf-8"), filename=str(cli_path))
    aliases = extract_alias_maps(tree, cli_path, root=root)

    # parse_file_to_ast should map to base module dpylens.analyzer.parser
    assert aliases.symbol_aliases["parse_file_to_ast"] == "dpylens.analyzer.parser"