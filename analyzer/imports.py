from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.models import ImportRecord


def _normalize_import(module: str | None) -> str | None:
    if not module:
        return None
    return module.strip() or None


def extract_imports(tree: ast.AST, file_path: Path) -> ImportRecord:
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = _normalize_import(node.module)
            if mod:
                imports.add(mod)

    return ImportRecord(file=str(file_path), imports=sorted(imports))