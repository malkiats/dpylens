from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

from dpylens.analyzer.imports import ImportRecord


@dataclass(frozen=True)
class PatternHit:
    file: str
    patterns: list[str]


def _has_import(imports: set[str], prefix: str) -> bool:
    return any(i == prefix or i.startswith(prefix + ".") for i in imports)


def _has_call(tree: ast.AST, names: set[str]) -> bool:
    """
    Detect simple calls like subprocess.run(), os.system(), etc.
    MVP: checks direct attribute names or function names.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in names:
                return True
            if isinstance(fn, ast.Attribute) and fn.attr in names:
                return True
    return False


def detect_patterns(tree: ast.AST, import_record: ImportRecord, file_path: Path) -> PatternHit:
    imports = set(import_record.imports)
    patterns: list[str] = []

    # CLI frameworks
    if _has_import(imports, "argparse") or _has_import(imports, "click") or _has_import(imports, "typer") or _has_import(imports, "fire"):
        patterns.append("devops:cli")

    # Shell / OS automation
    if _has_import(imports, "subprocess") or _has_import(imports, "shlex") or _has_import(imports, "os"):
        if _has_call(tree, {"system", "run", "Popen"}):
            patterns.append("devops:shell")

    # IaC
    if _has_import(imports, "pulumi") or any(i.startswith("pulumi_") for i in imports):
        patterns.append("iac:pulumi")
    if _has_import(imports, "aws_cdk") or _has_import(imports, "constructs"):
        patterns.append("iac:cdk")

    # Pipelines / Orchestrators
    if _has_import(imports, "airflow"):
        patterns.append("pipeline:airflow")
    if _has_import(imports, "prefect"):
        patterns.append("pipeline:prefect")
    if _has_import(imports, "dagster"):
        patterns.append("pipeline:dagster")
    if _has_import(imports, "luigi"):
        patterns.append("pipeline:luigi")

    # Models / Schemas
    if _has_import(imports, "pydantic"):
        patterns.append("models:pydantic")
    if _has_import(imports, "dataclasses"):
        patterns.append("models:dataclass")

    return PatternHit(file=str(file_path), patterns=sorted(set(patterns)))