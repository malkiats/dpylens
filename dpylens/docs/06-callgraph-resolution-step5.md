# Step 5 — Cross-Module Call Graph Resolution (MVP)

## Problem
Basic call graphs often show:
- `parse_file_to_ast`
- `parser.parse_file_to_ast`
But do not explain *which module* that function belongs to.

## Solution
We resolve calls using import alias information per file:
- `import dpylens.analyzer.parser as p` => p -> dpylens.analyzer.parser
- `from dpylens.analyzer.parser import parse_file_to_ast` => parse_file_to_ast -> dpylens.analyzer.parser

Then:
- `p.parse_file_to_ast()` -> dpylens.analyzer.parser.parse_file_to_ast
- `parse_file_to_ast()` -> dpylens.analyzer.parser.parse_file_to_ast

## Output
- `analysis/callgraph_resolved.json` includes:
  - caller
  - callee_raw
  - callee_resolved (if resolved)

## Limitations (MVP)
- Does not resolve dynamic imports
- Does not resolve method calls on objects
- Does not do type inference
- Relative import aliasing can be improved later