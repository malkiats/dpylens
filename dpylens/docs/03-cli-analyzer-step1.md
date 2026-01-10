# Step 1 (Code Generation): CLI skeleton + scanner + AST parser + JSON outputs + simple visualization

## We’ll implement the minimum working vertical slice:

dpylens analyze <path> --out <dir>:
- finds .py files
- parses AST safely
- extracts imports and call graph
- writes JSON outputs
- writes Graphviz DOT files (visualization you can render)
- This is best practice because you get something usable early, and we can extend - it with patterns + dataflow next.

# Files to add (copy into your repo)

## 1 pyproject.toml (CLI entry + deps)
(Only dependency needed for now is graphviz Python package for convenience; DOT output itself does not require it. You can render DOT with system graphviz.)


# Step 1 — CLI Analyzer (JSON + DOT output)

## What we built
A working CLI command:

- `dpylens analyze <path> --out <dir>`

It does:
1. Scan for `*.py` files (ignoring venv/build/.git)
2. Parse each file into an AST (safe; collects errors)
3. Extract:
   - imports (dependency data)
   - call graph (functions + call edges)
4. Outputs:
   - JSON:
     - `modules.json`
     - `callgraph.json`
   - Graphviz DOT:
     - `imports.dot`
     - `callgraph.dot`
     - `callgraph_grouped.dot`

## Why this is best practice
- Produces stable artifacts (JSON/DOT) that other layers can consume
- Works even if some files have syntax errors (does not crash)
- Simple extraction rules that are easy to extend

## How to run locally
### Install
From repo root:
- `python -m venv .venv`
- `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows)
- `pip install -e .`

### Run analyzer
- `dpylens analyze . --out analysis`

## Visualize DOT graphs
Install Graphviz (system package) then:

- `dot -Tpng analysis/imports.dot -o analysis/imports.png`
- `dot -Tpng analysis/callgraph.dot -o analysis/callgraph.png`
- `dot -Tpng analysis/callgraph_grouped.dot -o analysis/callgraph_grouped.png`

## Next step
Add:
- Pattern detection (`patterns.json`)
- Data flow heuristics (`dataflow.json`)