from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.models import CallRecord, FunctionRecord


def _callee_name(call: ast.Call) -> str:
    """
    Convert an ast.Call to a readable callee name.

    MVP+:
    - foo() -> "foo"
    - obj.method() -> "obj.method" if obj is a simple name
    - pkg.mod.fn() -> "<expr>.fn" (we keep attribute chain as best we can)
    """
    fn = call.func

    if isinstance(fn, ast.Name):
        return fn.id

    if isinstance(fn, ast.Attribute):
        # Try to reconstruct "a.b.c" where possible
        parts: list[str] = [fn.attr]
        cur = fn.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            parts.reverse()
            return ".".join(parts)

        # Unknown receiver expression
        parts.reverse()
        return "<expr>." + ".".join(parts)

    return "<unknown>"


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.functions: list[FunctionRecord] = []
        self.calls: list[CallRecord] = []
        self._stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        qual = f"{self.module_name}.{node.name}"
        self.functions.append(FunctionRecord(qualname=qual, file=str(self.file_path), lineno=node.lineno))
        self._stack.append(qual)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        qual = f"{self.module_name}.{node.name}"
        self.functions.append(FunctionRecord(qualname=qual, file=str(self.file_path), lineno=node.lineno))
        self._stack.append(qual)
        self.generic_visit(node)
        self._stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        if self._stack:
            caller = self._stack[-1]
            callee = _callee_name(node)
            lineno = getattr(node, "lineno", 0) or 0
            self.calls.append(CallRecord(caller=caller, callee=callee, file=str(self.file_path), lineno=lineno))
        self.generic_visit(node)


def extract_callgraph(tree: ast.AST, file_path: Path, module_name: str) -> tuple[list[FunctionRecord], list[CallRecord]]:
    v = CallGraphVisitor(file_path=file_path, module_name=module_name)
    v.visit(tree)
    return v.functions, v.calls