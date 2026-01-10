from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dpylens.analyzer.aliases import AliasMaps
from dpylens.analyzer.models import CallRecord, FunctionRecord


@dataclass(frozen=True)
class ResolvedCall:
    caller: str
    callee_raw: str
    callee_resolved: str | None
    file: str
    lineno: int


def _resolve_callee(
    callee_raw: str,
    *,
    alias: AliasMaps,
    local_functions: set[str],
) -> str | None:
    """
    Resolve a raw callee string into a fully qualified function if possible.

    Supported:
    - direct imported symbol:
        from X import fn
        fn() -> X.fn
    - module alias receiver:
        import dpylens.analyzer.parser as p
        p.parse_file_to_ast() -> dpylens.analyzer.parser.parse_file_to_ast
    - module imported by last name:
        import dpylens.analyzer.parser
        parser.parse_file_to_ast() -> dpylens.analyzer.parser.parse_file_to_ast
    - already-qualified call that matches local function
    """
    # already-qualified
    if callee_raw in local_functions:
        return callee_raw

    # direct function call: "fn"
    if "." not in callee_raw:
        base_mod = alias.symbol_aliases.get(callee_raw)
        if base_mod:
            candidate = f"{base_mod}.{callee_raw}"
            if candidate in local_functions:
                return candidate
        return None

    # attribute call: "receiver.fn"
    receiver, fn = callee_raw.split(".", 1)

    # receiver could be a module alias -> module path
    mod = alias.module_aliases.get(receiver)
    if mod:
        candidate = f"{mod}.{fn}"
        if candidate in local_functions:
            return candidate

    # receiver could be directly a module name (rare) - not handled in MVP
    return None


def resolve_calls(
    *,
    functions: list[FunctionRecord],
    calls: list[CallRecord],
    alias_maps_by_file: dict[str, AliasMaps],
    local_module_index: dict[str, Path],
) -> list[ResolvedCall]:
    local_functions = {f.qualname for f in functions}

    resolved: list[ResolvedCall] = []
    for c in calls:
        alias = alias_maps_by_file.get(c.file)
        callee_resolved = None
        if alias:
            callee_resolved = _resolve_callee(c.callee, alias=alias, local_functions=local_functions)
        resolved.append(
            ResolvedCall(
                caller=c.caller,
                callee_raw=c.callee,
                callee_resolved=callee_resolved,
                file=c.file,
                lineno=c.lineno,
            )
        )
    return resolved