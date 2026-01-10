# Core Engine (Code Analyzer & Visualizer) — Notes

## Purpose
Build a static analysis engine for Python DevOps projects that can:
- parse code safely (AST)
- map module dependencies (imports)
- build a call graph (who calls who)
- detect project patterns (IaC, CLI scripts, pipelines, models)
- extract basic data flow signals (inputs → outputs)

## Output (MVP)
We will output JSON so the visualization layer can consume it easily:
- analysis/modules.json
- analysis/callgraph.json
- analysis/patterns.json
- analysis/dataflow.json

## MVP Rules
- Do not crash on one bad file: collect errors per file
- Keep rules simple and extendable (pattern rules in one module)
- Prefer clear JSON formats over premature visualization

## Planned Modules
- scanner.py: find Python files
- parser.py: parse AST safely
- imports.py: extract imports
- callgraph.py: extract function definitions + calls
- patterns.py: detect "what kind of code this is"
- dataflow.py: detect inputs and outputs (heuristics)
- models.py: dataclasses for outputs

## Data Flow (MVP Heuristics)
Inputs:
- input()
- os.getenv / os.environ
- argparse / sys.argv
- file reads (open(..., "r"))

Outputs:
- print()
- file writes (open(..., "w"), .write())
- subprocess.run / os.system
- network writes (requests.post/put) [later]

Transforms:
- function calls and key operations between inputs and outputs (approximation)

## Next After MVP
- resolve local imports into a real module graph
- add caching (hashing files)
- output Graphviz/DOT for quick graphs
- integrate with a web UI
