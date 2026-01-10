from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dpylens.analyzer.imports import ImportItem, ImportRecord


@dataclass(frozen=True)
class ModuleNode:
    module: str
    file: str


@dataclass(frozen=True)
class ModuleEdge:
    src_module: str
    dst_module: str
    kind: str  # "local" or "external"
    raw_import: str


def module_name_for_file(root: Path, file_path: Path) -> str:
    rel = file_path.resolve().relative_to(root.resolve())
    no_suffix = rel.with_suffix("")
    return ".".join(no_suffix.parts)


def build_local_module_index(root: Path, py_files: list[Path]) -> dict[str, Path]:
    idx: dict[str, Path] = {}
    for f in py_files:
        idx[module_name_for_file(root, f)] = f
    return idx


def _is_init_module(mod: str) -> bool:
    return mod.endswith(".__init__")


def _package_name_for_init(mod: str) -> str:
    return mod[: -len(".__init__")]


def _expand_local_importables(local_modules: set[str]) -> set[str]:
    """
    If a package has __init__.py, treat the package name as importable.
    Example:
      dpylens.analyzer.__init__ exists => dpylens.analyzer is importable
    """
    expanded = set(local_modules)
    for m in list(local_modules):
        if _is_init_module(m):
            expanded.add(_package_name_for_init(m))
    return expanded


def _resolve_relative(module: str | None, level: int, src_module: str) -> str | None:
    """
    Resolve relative import base module against src_module.

    src_module includes the module of the file itself (e.g. dpylens.analyzer.cli)
    level=1 => from .X import Y  (go up 1 => dpylens.analyzer)
    level=2 => from ..X import Y (go up 2 => dpylens)
    """
    if level <= 0:
        return module

    src_parts = src_module.split(".")
    if len(src_parts) < level:
        return None

    base = src_parts[:-level]
    if module:
        return ".".join(base + module.split("."))
    return ".".join(base)


def _dedup_keep_order(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for x in items:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def _local_targets_for_import_item(
    item: ImportItem,
    *,
    src_module: str,
    local_importables: set[str],
) -> list[str]:
    """
    Convert one ImportItem into 0..N local module targets.

    Rules:
    - import A.B.C         -> try A.B.C (or A.B.C as package name)
    - from X import Y      -> try X, and also X.Y (if exists locally)
    - relative imports are resolved first
    """
    if item.kind == "import":
        base = item.module
        if not base:
            return []
        if base in local_importables:
            return [base]
        return []

    # from-import
    abs_base = _resolve_relative(item.module, item.level, src_module=src_module)
    if not abs_base:
        return []

    candidates: list[str] = []

    # base module/package itself
    if abs_base in local_importables:
        candidates.append(abs_base)

    # base.name modules/packages
    for name in item.names:
        guess = f"{abs_base}.{name}"
        if guess in local_importables:
            candidates.append(guess)

    return _dedup_keep_order(candidates)


def build_module_graph(
    *,
    root: Path,
    py_files: list[Path],
    import_records: list[ImportRecord],
) -> tuple[list[ModuleNode], list[ModuleEdge]]:
    local_index = build_local_module_index(root, py_files)
    local_modules = set(local_index.keys())
    local_importables = _expand_local_importables(local_modules)

    file_to_module = {str(p): module_name_for_file(root, p) for p in py_files}

    nodes: list[ModuleNode] = [
        ModuleNode(module=m, file=str(p)) for m, p in sorted(local_index.items(), key=lambda x: x[0])
    ]
    edges: list[ModuleEdge] = []

    for rec in import_records:
        src_mod = file_to_module.get(rec.file)
        if not src_mod:
            continue

        for item in rec.items:
            local_targets = _local_targets_for_import_item(
                item,
                src_module=src_mod,
                local_importables=local_importables,
            )

            if local_targets:
                for t in local_targets:
                    edges.append(
                        ModuleEdge(
                            src_module=src_mod,
                            dst_module=t,
                            kind="local",
                            raw_import=item.raw,
                        )
                    )
            else:
                # Keep an external edge so users can still see dependencies
                # Choose best-available name
                if item.kind == "import":
                    dst = item.module or "<unknown>"
                else:
                    # include relative dots for readability
                    dst = ("." * item.level) + (item.module or "")
                    dst = dst or "<unknown>"

                edges.append(
                    ModuleEdge(
                        src_module=src_mod,
                        dst_module=dst,
                        kind="external",
                        raw_import=item.raw,
                    )
                )

    return nodes, edges