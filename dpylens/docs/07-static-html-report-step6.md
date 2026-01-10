# Step 6 — Static HTML Report (Zero Deps)

## Goal
Generate a simple UI without React:
- one HTML file
- loads analysis JSON files
- shows summary + tables
- shows graph images if present

## Command
1) Generate analysis:
- `dpylens analyze . --out analysis`

2) Generate report:
- `dpylens report --analysis analysis --out report`

## View report
Browsers often block `fetch()` for local `file://` paths.
So serve it locally:

- `cd report`
- `python -m http.server`
- open `http://localhost:8000`

## Output folder
`report/`
- `index.html`
- `data/*.json`
- `img/*.png` (copied if exists)