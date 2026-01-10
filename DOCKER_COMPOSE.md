# Run dpylens (API + Web) with Docker Compose

This runs:
- **API** (FastAPI + dpylens runner) on `http://localhost:8787`
- **Web** (React build served by nginx) on `http://localhost:5173`

It also persists analysis runs (cloned repos + generated report bundles) in a local folder:
- `./.dpylens-server/`

---

## 0) Prerequisites

- Docker Desktop (or Docker Engine) with Compose support:
  ```bash
  docker --version
  docker compose version
  ```

---

## 1) Files expected in the repo

At repo root:
- `Dockerfile` (API image)
- `docker-compose.yml`
- `.dockerignore`

Under `web/`:
- `web/Dockerfile`

---

## 2) Build + start

From the repo root:

```bash
docker compose up --build
```

This will:
- build the API container
- build the Web container (Vite → `dist/` → nginx)
- start both containers

---

## 3) Open in browser

- Web UI: **http://localhost:5173**
- API health: **http://localhost:8787/health**

---

## 4) Run an analysis from the Web UI

1. Open **http://localhost:5173**
2. Paste a public GitHub repo URL (example):
   - `https://github.com/malkiats/test-lapwing`
3. Click **Run Analysis**
4. Wait until it completes
5. The report will appear embedded in the page

Artifacts are stored on your machine at:
- `./.dpylens-server/runs/<run_id>/`

---

## 5) Run an analysis from the command line (optional)

Health check:
```bash
curl http://127.0.0.1:8787/health
```

Analyze:
```bash
curl -X POST http://127.0.0.1:8787/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/malkiats/test-lapwing","render":true}'
```

The response includes:
- `run_id`
- `report_url` like `/runs/<run_id>/report/`

Open the embedded report directly:
```text
http://127.0.0.1:8787/runs/<run_id>/report/
```

---

## 6) Stop / cleanup

Stop containers:
```bash
docker compose down
```

Remove all stored run artifacts:
```bash
rm -rf ./.dpylens-server
```

---

## Notes / troubleshooting

### Web can’t call the API
By default the frontend calls `http://localhost:8787` from your browser.
Make sure:
- API container is running
- port `8787` is free on your machine
- you can access: `http://localhost:8787/health`

### Graph PNGs don’t appear in the report
The API image installs `graphviz` and should be able to render PNGs.
If you set `"render": false` in the request, PNGs won’t be generated.

### Repo clone fails (private repos)
The current API supports public repos only (no auth token flow yet).

---

## Recommended `.gitignore`
Make sure this is ignored so you don’t commit run artifacts:
```gitignore
.dpylens-server/
```