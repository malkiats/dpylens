from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportItem:
    """
    A structured representation of an import statement.

    kind:
      - "import":        import X
      - "from":          from X import Y
    module:
      - for "import": module is the imported module (e.g. "os", "dpylens.cli")
      - for "from":   module is the base module (e.g. "dpylens.analyzer"), can be None
    level:
      - 0 = absolute import
      - >0 = relative import (number of dots)
    names:
      - names imported in a "from" import (aliases ignored for MVP)
    raw:
      - raw string for debugging
    """
    kind: str
    module: str | None
    level: int
    names: list[str]
    raw: str


@dataclass(frozen=True)
class ImportRecord:
    file: str
    imports: list[str]      # flattened base modules (legacy/quick rules)
    items: list[ImportItem] # structured info for accurate resolution


def extract_imports(tree: ast.AST, file_path: Path) -> ImportRecord:
    flat: set[str] = set()
    items: list[ImportItem] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not alias.name:
                    continue
                flat.add(alias.name)
                items.append(
                    ImportItem(
                        kind="import",
                        module=alias.name,
                        level=0,
                        names=[],
                        raw=f"import {alias.name}",
                    )
                )

        elif isinstance(node, ast.ImportFrom):
            mod = node.module  # can be None
            level = int(node.level or 0)
            names = [a.name for a in (node.names or []) if a.name]

            if mod:
                flat.add(mod)

            raw_mod = ("." * level) + (mod or "")
            raw = f"from {raw_mod} import {', '.join(names) if names else '*'}"

            items.append(
                ImportItem(
                    kind="from",
                    module=mod,
                    level=level,
                    names=names,
                    raw=raw,
                )
            )

    return ImportRecord(file=str(file_path), imports=sorted(flat), items=items)