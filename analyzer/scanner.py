from __future__ import annotations

from pathlib import Path

DEFAULT_EXCLUDES = {
    ".git",
    ".hg",
    ".svn",
    ".tox",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
}


def scan_python_files(root: Path, excludes: set[str] | None = None) -> list[Path]:
    """
    Recursively find *.py files under root.

    Best practices:
    - ignore virtualenv/build/git folders
    - return sorted paths for stable output
    """
    root = root.resolve()
    ex = DEFAULT_EXCLUDES if excludes is None else excludes

    files: list[Path] = []
    for p in root.rglob("*.py"):
        # Skip if any part of the path is excluded
        if any(part in ex for part in p.parts):
            continue
        files.append(p)

    return sorted(files)