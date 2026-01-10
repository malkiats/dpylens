from __future__ import annotations

from pathlib import Path

from dpylens.analyzer.layout import detect_package_layout, module_name_for_file_with_layout


def test_monorepo_packages_src_layout_module_name(tmp_path: Path) -> None:
    repo = tmp_path / "repo"

    # packages/pkgA/src/pkgA/util.py
    util = repo / "packages" / "pkgA" / "src" / "pkgA" / "util.py"
    util.parent.mkdir(parents=True)
    (util.parent / "__init__.py").write_text("", encoding="utf-8")
    util.write_text("x = 1\n", encoding="utf-8")

    layout = detect_package_layout(repo)

    assert (repo / "packages" / "pkgA" / "src") in layout.package_roots
    assert module_name_for_file_with_layout(layout, util) == "pkgA.util"