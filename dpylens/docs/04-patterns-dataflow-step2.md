# Step 2 — Patterns + Data Flow (MVP)

## Pattern Recognition
We detect common DevOps-related code types using simple rules:
- devops:cli -> argparse/click/typer/fire imports
- devops:shell -> subprocess/os.system usage
- iac:pulumi -> pulumi imports
- iac:cdk -> aws_cdk/constructs imports
- pipeline:* -> airflow/prefect/dagster/luigi imports
- models:* -> pydantic/dataclasses imports

Output: `analysis/patterns.json`

## Data Flow (Heuristic)
We approximate data flow using "signals", not full program analysis.

Inputs:
- input()
- os.getenv / os.environ
- open(..., "r")

Outputs:
- print()
- open(..., "w"/"a")
- subprocess.run / os.system

Transforms:
- record called function names as a simple “steps list”

Output: `analysis/dataflow.json` and optional `analysis/dataflow.dot`

## Why heuristic?
True static data flow requires advanced analysis.
The heuristic approach gives useful diagrams fast and is easy to improve later.