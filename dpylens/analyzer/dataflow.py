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


def _is_open_with_mode(call: ast.Call, modes: set[str]) -> bool:
    # open("x", "r") or open("x", mode="r")
    if not isinstance(call.func, ast.Name) or call.func.id != "open":
        return False

    # positional mode argument
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
        return call.args[1].value in modes

    # keyword mode argument
    for kw in call.keywords or []:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value in modes

    return False


def _call_name(node: ast.Call) -> str:
    fn = node.func
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return "<unknown>"


class DataFlowVisitor(ast.NodeVisitor):
    def __init__(self, file_path: Path, module_name: str):
        self.file_path = file_path
        self.module_name = module_name
        self.results: list[FunctionDataFlow] = []
        self._current_func: str | None = None
        self._current_lineno: int = 0
        self._inputs: set[str] = set()
        self._outputs: set[str] = set()
        self._transforms: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._start_function(node.name, node.lineno)
        self.generic_visit(node)
        self._finish_function()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._start_function(node.name, node.lineno)
        self.generic_visit(node)
        self._finish_function()

    def _start_function(self, name: str, lineno: int) -> None:
        self._current_func = f"{self.module_name}.{name}"
        self._current_lineno = lineno
        self._inputs = set()
        self._outputs = set()
        self._transforms = []

    def _finish_function(self) -> None:
        assert self._current_func is not None
        self.results.append(
            FunctionDataFlow(
                function=self._current_func,
                file=str(self.file_path),
                lineno=self._current_lineno,
                inputs=sorted(self._inputs),
                transforms=self._transforms,
                outputs=sorted(self._outputs),
            )
        )
        self._current_func = None

    def visit_Call(self, node: ast.Call) -> None:
        if not self._current_func:
            return

        name = _call_name(node)

        # INPUTS
        if isinstance(node.func, ast.Name) and node.func.id == "input":
            self._inputs.add("stdin:input()")

        # env reads: os.getenv("X")
        if isinstance(node.func, ast.Attribute) and node.func.attr == "getenv":
            self._inputs.add("env:os.getenv")

        # file read/write via open
        if _is_open_with_mode(node, {"r", "rt", "rb"}):
            self._inputs.add("file:open(read)")
        if _is_open_with_mode(node, {"w", "wt", "wb", "a", "at", "ab"}):
            self._outputs.add("file:open(write)")

        # OUTPUTS
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            self._outputs.add("stdout:print()")

        # subprocess usage
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"run", "Popen"}:
            self._outputs.add("subprocess:exec")

        if isinstance(node.func, ast.Attribute) and node.func.attr == "system":
            self._outputs.add("subprocess:os.system")

        # TRANSFORMS (simple “steps list”)
        # Keep it simple: record every call name except very common IO ones
        if name not in {"print", "input", "open"}:
            self._transforms.append(name)

        self.generic_visit(node)


def extract_dataflow(tree: ast.AST, file_path: Path, module_name: str) -> list[FunctionDataFlow]:
    v = DataFlowVisitor(file_path=file_path, module_name=module_name)
    v.visit(tree)
    return v.results