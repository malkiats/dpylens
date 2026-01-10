from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    ".tox",
    "build",
    "dist",
    ".eggs",
    "site-packages",
    "node_modules",
}


@dataclass(frozen=True)
class PackageLayout:
    """
    package_roots: directories that should be treated as the root for module naming.
    Example:
      - repo root: /repo
      - src root:  /repo/src
      - monorepo:  /repo/packages/pkgA/src, /repo/packages/pkgB/src
    """
    repo_root: Path
    package_roots: list[Path]


def _has_python_package(dir_path: Path) -> bool:
    if not dir_path.is_dir():
        return False
    if (dir_path / "__init__.py").exists():
        return True
    return any(p.suffix == ".py" for p in dir_path.glob("*.py"))


def _src_looks_like_python(src_dir: Path) -> bool:
    """
    Heuristic: src contains at least one candidate package directory.
    """
    if not src_dir.exists() or not src_dir.is_dir():
        return False
    candidates = [p for p in src_dir.iterdir() if p.is_dir() and p.name not in DEFAULT_IGNORE_DIRS]
    return any(_has_python_package(c) for c in candidates)


def detect_package_layout(repo_root: Path) -> PackageLayout:
    repo_root = repo_root.resolve()
    roots: list[Path] = []

    # Prefer src/ if present
    top_src = repo_root / "src"
    if _src_looks_like_python(top_src):
        roots.append(top_src.resolve())

    # Monorepo convention: packages/*/src
    packages_dir = repo_root / "packages"
    if packages_dir.exists() and packages_dir.is_dir():
        for pkg in sorted(packages_dir.iterdir()):
            if not pkg.is_dir():
                continue
            if pkg.name in DEFAULT_IGNORE_DIRS:
                continue
            pkg_src = pkg / "src"
            if _src_looks_like_python(pkg_src):
                roots.append(pkg_src.resolve())

    # Always include repo_root as fallback
    roots.append(repo_root)

    # De-dupe while preserving order
    uniq: list[Path] = []
    for r in roots:
        if r not in uniq:
            uniq.append(r)

    return PackageLayout(repo_root=repo_root, package_roots=uniq)


def module_name_for_file_with_layout(layout: PackageLayout, file_path: Path) -> str:
    file_path = file_path.resolve()

    chosen_root: Path | None = None
    for r in layout.package_roots:
        try:
            file_path.relative_to(r)
            chosen_root = r
            break
        except ValueError:
            continue

    if chosen_root is None:
        chosen_root = layout.repo_root

    rel = file_path.relative_to(chosen_root)
    rel_no_suffix = rel.with_suffix("")
    return ".".join(rel_no_suffix.parts)