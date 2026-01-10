from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class FileError:
    file: str
    error: str


@dataclass(frozen=True)
class FunctionRecord:
    qualname: str
    file: str
    lineno: int


@dataclass(frozen=True)
class CallRecord:
    caller: str
    callee: str
    file: str
    lineno: int


def to_jsonable(obj: Any) -> Any:
    """Convert dataclasses (and nested lists) to plain JSON-serializable data."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    return obj