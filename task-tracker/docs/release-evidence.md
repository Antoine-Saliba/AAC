# Release Evidence

## Baseline
- Branch: final-project
- Date: 2026-08-12
- Local app run command: `python -m app.main` (run from `task-tracker/backend`, venv active)
- /health result: `curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://127.0.0.1:8000/health` → `{"status":"ok","timestamp":"2026-08-12T07:41:46.469403+00:00"}` / HTTP_STATUS:200
- Frontend check:Opened http://127.0.0.1:8000/ in Edge; the Kanban board renders with To Do / In Progress / Done columns and per-column counts. Created a task via New Task and it appeared in In Progress with its priority badge; opened Edit, changed the title, saved, and the change persisted after a page refresh.
- Test command: `pytest -v`
- Test result: 42 passed, 2 warnings in 1.25s

## CI evidence
- Workflow file: `.github/workflows/ci.yml` (ALREADY SATISFIED — triggers on push and pull_request, pins Python 3.11, installs from `task-tracker/backend/requirements.txt`, runs `pytest -v`; no changes made)
- Latest run link or note: https://github.com/Antoine-Saliba/AAC/actions/runs/31580989916
- Test command used by CI: `pytest -v`
- Shortcut check:
  - `continue-on-error`: absent
  - `|| true`: absent
  - pytest step commented out/skipped/conditional: absent (unconditional `run: pytest -v` step)
  - missing dependency install step: absent (`pip install -r requirements.txt` present)
  - unpinned or vague Python version: absent (pinned to `"3.11"`)

## Docker evidence
- Build command: `docker build -t task-tracker-api .` (run from `task-tracker/`) — succeeded, image `task-tracker-api:latest` built
- Run command: `docker run -d --rm -p 8001:8000 --name task-tracker-verify task-tracker-api` (host port 8001 used, not 8000, because the local `python -m app.main` dev server from an earlier step was already bound to host port 8000)
- /health check: `curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://127.0.0.1:8001/health` → `{"status":"ok","timestamp":"2026-08-12T07:49:16.784581+00:00"}` / HTTP_STATUS:200
- Non-root check, if implemented: implemented and verified — `docker exec task-tracker-verify whoami` → `app`; `id` → `uid=1000(app) gid=1000(app) groups=1000(app)`
- No-baked-secrets check: verified — `find /app -maxdepth 3` inside the running container listed only `frontend/index.html` and `backend/app/*.py`; no `.env`, `requirements.txt`, `tests/`, `docs/`, or `.git` present in the image. `.dockerignore` also explicitly excludes `.env`, `**/.env`, `.git`, `venv/`, `.venv/`, `__pycache__/`, `.pytest_cache/`.

## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| `GET /health` returns HTTP 200 with `{"status": "ok", "timestamp": "..."}` (README §4) | `curl -s -w "\nHTTP_STATUS:%{http_code}\n" http://127.0.0.1:8000/health` → `{"status":"ok","timestamp":"2026-08-12T07:41:46.469403+00:00"}` / HTTP_STATUS:200 | ACCURATE | None |
| Docker image builds with `docker build -t task-tracker-api .`, runs as non-root, does not bake in `.env` (README §6) | `docker build`/`docker run` succeeded; `docker exec ... whoami` → `app`; `id` → `uid=1000(app)`; `find /app -maxdepth 3` in the running container showed no `.env`/`requirements.txt`/`tests`/`docs`/`.git` | ACCURATE | None |
| CI triggers on push and pull_request, Python 3.11, working-dir `task-tracker/backend`, checkout → setup-python → install → `pytest -v` (README §7) | Direct read of `.github/workflows/ci.yml` lines 3-26 | ACCURATE | None |
