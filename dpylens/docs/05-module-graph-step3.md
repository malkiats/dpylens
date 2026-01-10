# Step 3 — Improved Module Dependency Graph (Local Edges)

## Problem
In Step 1, imports were stored as strings:
- file -> "os"
- file -> "dpylens.analyzer.parser"

This is not enough to build a real dependency graph between *your own* files.

## Solution
We build an index of local modules by scanning all `*.py` files:
- file path -> module name (dpylens.analyzer.parser)

Then we resolve imports:
- If an import matches a local module, create a **local edge**
- Otherwise keep it as an **external edge**

## Outputs
- `analysis/module_graph.json` (nodes + edges)
- `analysis/module_graph.dot` (blue edges=local, gray edges=external)

## Notes
This is MVP resolution. It will improve later by:
- resolving `from X import Y` more accurately
- handling packages and `__init__.py`
- handling `as` aliases and relative imports

dot -Tpng analysis/module_graph.dot -o analysis/module_graph.png