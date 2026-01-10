from __future__ import annotations

from pathlib import Path

from dpylens.analyzer.modulegraph import module_name_for_file


def test_module_name_for_file_basic(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pkg = root / "dpylens" / "analyzer"
    pkg.mkdir(parents=True)

    f = pkg / "parser.py"
    f.write_text("# test\n", encoding="utf-8")

    assert module_name_for_file(root, f) == "dpylens.analyzer.parser"


def test_module_name_for_file_init(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    pkg = root / "dpylens" / "analyzer"
    pkg.mkdir(parents=True)

    f = pkg / "__init__.py"
    f.write_text("# init\n", encoding="utf-8")

    assert module_name_for_file(root, f) == "dpylens.analyzer.__init__"