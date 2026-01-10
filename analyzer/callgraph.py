from __future__ import annotations

import ast
from pathlib import Path

from dpylens.analyzer.models import CallRecord, FunctionRecord


def _callee_name(call: ast.Call) -> str:
    """
    Convert an ast.Call to a readable callee name.

    MVP rules:
    - foo() -> "foo"
    - obj.method() -> "*.method" (unknown receiver)
    - nested like pkg.mod.fn() -> "*.fn"
    """
    fn = call.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return f"*.{fn.attr}"
    return "<unknown>"


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.functions: list[FunctionRecord] = []
        self.calls: list[CallRecord] = []
        self._stack: list[str] = []  # current function qualname stack

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
            self.calls.append(
                CallRecord(caller=caller, callee=callee, file=str(self.file_path), lineno=lineno)
            )
        self.generic_visit(node)


def extract_callgraph(tree: ast.AST, file_path: Path, module_name: str) -> tuple[list[FunctionRecord], list[CallRecord]]:
    v = CallGraphVisitor(file_path=file_path, module_name=module_name)
    v.visit(tree)
    return v.functions, v.calls