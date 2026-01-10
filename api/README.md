# dpylens API (local dev)

## Install
```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# important: dpylens must be installed in editable mode in your main repo
cd ..
pip install -e .
```

## Run
```bash
cd api
uvicorn main:app --reload --port 8787
```

## Endpoints
- `GET /health`
- `POST /analyze` JSON:
  - `{ "repo_url": "https://github.com/owner/repo", "render": true }`

Downloads:
- `/runs/<run_id>/report.zip`
- `/runs/<run_id>/analysis.zip`