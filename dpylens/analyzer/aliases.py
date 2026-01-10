from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AliasMaps:
    """
    module_aliases:
      alias -> module
      e.g. import dpylens.analyzer.parser as p  =>  p -> dpylens.analyzer.parser
           import dpylens.analyzer.parser      =>  parser -> dpylens.analyzer.parser

    symbol_aliases:
      symbol -> module
      e.g. from dpylens.analyzer.parser import parse_file_to_ast => parse_file_to_ast -> dpylens.analyzer.parser
           from .parser import parse_file_to_ast                => parse_file_to_ast -> <resolved module>
    """
    file: str
    module_aliases: dict[str, str]
    symbol_aliases: dict[str, str]


def _module_name_from_path(root: Path, file_path: Path) -> str:
    """
    Same logic as CLI: root-relative module path.
    """
    rel = file_path.resolve().relative_to(root.resolve())
    no_suffix = rel.with_suffix("")
    return ".".join(no_suffix.parts)


def _resolve_relative(module: str | None, level: int, src_module: str) -> str | None:
    """
    Resolve relative import base module against src_module.

    src_module is the module of the current file (e.g. dpylens.analyzer.cli)

    Examples:
      src_module=dpylens.analyzer.cli
      from .parser import X    => module="parser", level=1 => dpylens.analyzer.parser
      from ..utils import X    => module="utils", level=2  => dpylens.utils
      from . import X          => module=None, level=1     => dpylens.analyzer
    """
    if level <= 0:
        return module

    parts = src_module.split(".")
    if len(parts) < level:
        return None

    base = parts[:-level]
    if module:
        return ".".join(base + module.split("."))
    return ".".join(base)


def extract_alias_maps(tree: ast.AST, file_path: Path, *, root: Path) -> AliasMaps:
    """
    Extract alias maps for resolving cross-module calls.

    IMPORTANT:
    - This version resolves relative imports using `root` and `file_path`.
    - Caller must pass repo root used for module naming consistency.
    """
    module_aliases: dict[str, str] = {}
    symbol_aliases: dict[str, str] = {}

    src_module = _module_name_from_path(root, file_path)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name:
                    continue
                asname = alias.asname or alias.name.split(".")[-1]
                module_aliases[asname] = alias.name

        elif isinstance(node, ast.ImportFrom):
            # node.module can be None for "from . import X"
            level = int(node.level or 0)
            base_abs = _resolve_relative(node.module, level, src_module=src_module)
            if not base_abs:
                continue

            for alias in node.names:
                if not alias.name:
                    continue
                asname = alias.asname or alias.name
                symbol_aliases[asname] = base_abs

    return AliasMaps(file=str(file_path), module_aliases=module_aliases, symbol_aliases=symbol_aliases)