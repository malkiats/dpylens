from __future__ import annotations

from pathlib import Path

from dpylens.analyzer.layout import detect_package_layout, module_name_for_file_with_layout


def test_src_layout_module_name(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    pkg = repo / "src" / "mypkg"
    pkg.mkdir(parents=True)

    (pkg / "__init__.py").write_text("", encoding="utf-8")
    f = pkg / "util.py"
    f.write_text("x = 1\n", encoding="utf-8")

    layout = detect_package_layout(repo)
    assert (repo / "src") in layout.package_roots

    assert module_name_for_file_with_layout(layout, f) == "mypkg.util"