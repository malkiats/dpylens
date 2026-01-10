# Step 8 — `dpylens run`

## Goal
One command to:
1) analyze a folder
2) (optionally) render PNGs if Graphviz is installed
3) generate a static HTML report

## Usage
```bash
dpylens run . --analysis-out analysis --report-out report --render
```

If Graphviz is not installed, the command will warn and still generate the report.

## View the report
```bash
cd report
python -m http.server
open http://localhost:8000
```