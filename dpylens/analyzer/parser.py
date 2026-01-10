from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.models import FileError


def parse_file_to_ast(path: Path) -> tuple[ast.AST | None, FileError | None]:
    """
    Parse a python file into an AST.

    Returns:
      (tree, None) on success
      (None, FileError) on failure
    """
    try:
        source = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return None, FileError(file=str(path), error=f"read_error: {e}")

    try:
        tree = ast.parse(source, filename=str(path))
        return tree, None
    except SyntaxError as e:
        return None, FileError(file=str(path), error=f"syntax_error: {e.msg} (line {e.lineno})")
    except Exception as e:  # noqa: BLE001
        return None, FileError(file=str(path), error=f"parse_error: {e}")