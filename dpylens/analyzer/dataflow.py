from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FunctionDataFlow:
    function: str
    file: str
    lineno: int
    inputs: list[str]
    transforms: list[str]
    outputs: list[str]


# Backwards-compat alias if anything imported DataflowRecord (from the brief replacement)
DataflowRecord = FunctionDataFlow


class DataflowVisitor(ast.NodeVisitor):
    """
    Heuristic dataflow extractor. Must never crash analysis.
    Uses a stack to correctly handle nested function definitions.
    """

    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.records: list[FunctionDataFlow] = []
        self._stack: list[dict] = []

    def _start_function(self, name: str, lineno: int, args: ast.arguments) -> None:
        params: list[str] = []
        for a in list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs):
            if getattr(a, "arg", None):
                params.append(a.arg)
        if args.vararg and args.vararg.arg:
            params.append(args.vararg.arg)
        if args.kwarg and args.kwarg.arg:
            params.append(args.kwarg.arg)

        self._stack.append(
            {
                "function": f"{self.module_name}.{name}",
                "lineno": lineno,
                "inputs": set(params),
                "transforms": [],
                "outputs": set(),
            }
        )

    def _finish_function(self) -> None:
        if not self._stack:
            return
        cur = self._stack.pop()
        self.records.append(
            FunctionDataFlow(
                function=cur["function"],
                file=str(self.file_path),
                lineno=int(cur["lineno"] or 0),
                inputs=sorted(cur["inputs"]),
                transforms=list(cur["transforms"]),
                outputs=sorted(cur["outputs"]),
            )
        )

    def _cur(self) -> dict | None:
        return self._stack[-1] if self._stack else None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._start_function(node.name, getattr(node, "lineno", 0) or 0, node.args)
        self.generic_visit(node)
        self._finish_function()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._start_function(node.name, getattr(node, "lineno", 0) or 0, node.args)
        self.generic_visit(node)
        self._finish_function()

    def visit_Call(self, node: ast.Call) -> None:
        cur = self._cur()
        if cur is not None:
            fn = node.func
            if isinstance(fn, ast.Name):
                cur["transforms"].append(fn.id)
            elif isinstance(fn, ast.Attribute):
                cur["transforms"].append(fn.attr)

            # crude env access signal
            if isinstance(fn, ast.Attribute) and fn.attr in {"get", "getenv"}:
                cur["inputs"].add("env:*")

        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        cur = self._cur()
        if cur is not None:
            cur["outputs"].add("return")
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        cur = self._cur()
        if cur is not None:
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    cur["outputs"].add(t.id)
        self.generic_visit(node)


def extract_dataflow(tree: ast.AST, file_path: Path, module_name: str) -> list[FunctionDataFlow]:
    v = DataflowVisitor(file_path=file_path, module_name=module_name)
    try:
        v.visit(tree)
    except Exception:
        return []
    return v.records