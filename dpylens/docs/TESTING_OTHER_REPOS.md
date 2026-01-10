# Testing dPyLens on other repositories (step-by-step)

This guide shows how to update your local `dpylens` CLI from `malkiats/dpylens` and run it on another repo (example: `malkiats/test-lapwing`) without polluting that repo.

---

## 0) Prerequisites

- Python (recommended: 3.11+; you are using 3.13 which is fine)
- (Optional) Graphviz for PNG rendering:
  - macOS: `brew install graphviz`
  - Linux: `sudo apt-get install graphviz`

To verify Graphviz:
```bash
dot -V
```

---

## 1) Update `malkiats/dpylens` locally and install it (editable)

```bash
cd ~/path/to/dpylens          # your cloned malkiats/dpylens
git checkout master
git pull origin master

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .              # editable install so changes apply immediately

dpylens --help                # sanity check
```

Notes:
- Keep this `.venv` and reuse it to run `dpylens` on all target repos.
- `pip install -e .` ensures changes in `malkiats/dpylens` are reflected immediately.

---

## 2) Clone or update the target repo (example: `malkiats/test-lapwing`)

```bash
cd ~/path/to/workspace

git clone https://github.com/malkiats/test-lapwing.git
# OR if you already have it:
cd test-lapwing
git pull origin master        # or main depending on that repo
```

---

## 3) Run `dpylens` on the target repo

Keep using the `dpylens` virtualenv from Step 1 (do NOT create a new venv in the target repo unless you want to).

```bash
# ensure you're still in the dpylens venv:
# (you should see (.venv) in your prompt)

cd ~/path/to/workspace/test-lapwing

dpylens run . \
  --analysis-out .dpylens-analysis \
  --report-out .dpylens-report \
  --render \
  --serve \
  --open
```

What this does:
- `--analysis-out .dpylens-analysis` writes all JSON/DOT/PNG analysis artifacts to a repo-local hidden folder.
- `--report-out .dpylens-report` writes the HTML report and copied JSON/PNGs there.
- `--render` generates PNG graphs from DOT **if** Graphviz `dot` is available (otherwise it warns and continues).
- `--serve --open` starts a local HTTP server for the report and opens it in your browser (so JSON `fetch()` works).

Stop the server with `Ctrl+C` in the terminal.

---

## 4) If the target repo uses `src/` layout (optional)

If the repo has code under `src/`, analyze that folder directly:

```bash
dpylens run src \
  --analysis-out .dpylens-analysis \
  --report-out .dpylens-report \
  --render \
  --serve \
  --open
```

---

## 5) Verify outputs

```bash
ls .dpylens-analysis
ls .dpylens-report
```

Common expected files:
- `.dpylens-analysis/modules.json`
- `.dpylens-analysis/callgraph.json`
- `.dpylens-analysis/callgraph_resolved.json`
- `.dpylens-analysis/module_graph.json`
- `.dpylens-analysis/dataflow.json`
- `.dpylens-report/index.html`

---

## 6) Prevent accidental commits in the target repo (recommended)

In the target repo (`test-lapwing`), add to `.gitignore`:

```gitignore
.dpylens-analysis/
.dpylens-report/
```

---

## 7) Troubleshooting

### Report shows "Failed to load report data"
You opened the report via `file://` and the browser blocked JSON `fetch()`.

Fix: always run with server mode:
```bash
dpylens run . --serve --open
```

### PNG graphs not showing
Install Graphviz and re-run with `--render`:
```bash
brew install graphviz
dpylens run . --render --serve --open
```

---

## 8) Next (optional) testing checklist
When testing new repos, capture:
- `tree -L 2` output of repo layout
- terminal output of `dpylens run ...`
- any warnings counts (shown in Overview)