from __future__ import annotations

from pathlib import Path

from dpylens.analyzer.layout import DEFAULT_IGNORE_DIRS


def scan_python_files(root: Path) -> list[Path]:
    root = root.resolve()
    files: list[Path] = []

    for p in root.rglob("*.py"):
        # skip ignored directories anywhere in the path
        if any(part in DEFAULT_IGNORE_DIRS for part in p.parts):
            continue
        files.append(p)

    return sorted(files)