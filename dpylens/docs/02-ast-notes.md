# Python AST Notes

## What is AST?
AST means **Abstract Syntax Tree**.
Python can turn source code into a tree structure where:
- "FunctionDef" nodes represent `def myfunc():`
- "Import" nodes represent `import x`
- "Call" nodes represent `something()`

## Why use AST?
It is safer and more accurate than regex searching because:
- it understands Python syntax
- it ignores comments and formatting
- it can locate line numbers

## Common Nodes We'll Use
- ast.Module: whole file
- ast.FunctionDef / ast.AsyncFunctionDef: functions
- ast.ClassDef: classes
- ast.Import / ast.ImportFrom: imports
- ast.Call: function calls
- ast.Attribute: things like obj.method
- ast.Name: simple names like foo

## MVP Strategy
We will not try to fully "understand" runtime behavior.
Instead, we will extract:
- structure (imports, functions, calls)
- signals (input/env/file reads; output/prints/file writes/subprocess)

This gives useful diagrams without complex program analysis.