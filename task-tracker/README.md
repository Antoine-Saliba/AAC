# Task Tracker

A learning-project REST API for tracking tasks, built with Python, FastAPI, and Pydantic, with a single-file Kanban frontend. This build adds a CI pipeline and a Docker image on top of the mid-course feature set (task CRUD, due dates/overdue, and task comments). [VERIFY: this repo doesn't label itself "Module 4" anywhere explicitly — inferred from the added CI/Docker tooling.]

Task and comment data live in an in-memory Python dict for the server's lifetime — **nothing is persisted to disk or a database**. The FastAPI app description currently says persistence is "backed by a local JSON file," but that's stale/aspirational text left over from an earlier plan; the actual behavior and reasoning are recorded in [`docs/midcourse/mini-adr.md`](docs/midcourse/mini-adr.md).

## 1. Project overview

- **Backend**: FastAPI + Pydantic REST API for tasks and per-task comments (`task-tracker/backend/`).
- **Frontend**: a single static HTML file with no build step, talking to the backend at a hardcoded `http://127.0.0.1:8000` (`task-tracker/frontend/index.html`).
- **Features**: task CRUD; optional `due_date` with a server-computed, read-only `overdue` flag; status-transition rules (forward-only moves); per-task comments (list/add/delete).
- **Scope**: this is a learning project. It does **not** implement authentication, a database, or any deployment/production configuration — see [Section 9](#9-project-conventions-and-current-limitations).

## 2. Prerequisites

- **Python 3.10+** — the codebase uses `X | None` union-type syntax (PEP 604), which requires 3.10 or newer. [VERIFY: CI itself pins exactly Python 3.11 — that's the only version actually tested automatically.]
- **pip** (comes with Python).
- **Docker** — only needed if you want to build/run the container (Section 6).

Check your Python version:

```bash
python --version
```

## 3. Local setup

Run from the repo root (the directory containing `task-tracker/`).

```bash
cd task-tracker/backend
python -m venv venv
```

Activate the virtual environment:

macOS / Linux:

```bash
source venv/bin/activate
```

Windows (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your local `.env` (git-ignored; `.env.example` is the committed reference):

```bash
cp .env.example .env
```

On Windows use `copy .env.example .env` instead of `cp`.

## 4. Run the app locally

From `task-tracker/backend`, with the virtual environment active:

```bash
uvicorn app.main:app --reload --port 8000
```

This starts the server at http://127.0.0.1:8000 with auto-reload enabled.

Interactive API docs are generated automatically:

- Swagger UI — http://127.0.0.1:8000/docs
- ReDoc — http://127.0.0.1:8000/redoc

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response, HTTP 200:

```json
{
  "status": "ok",
  "timestamp": "2026-07-23T10:15:30.123456+00:00"
}
```

**Frontend**: with the backend running, either open http://127.0.0.1:8000/ (served directly by the backend) or open `task-tracker/frontend/index.html` in a browser directly. The page talks to the backend at `http://127.0.0.1:8000`, so the backend must already be running.

`python -m app.main` (run from the same directory) is an alternative entry point already present in `app/main.py` — it reads `APP_ENV`/`PORT` from `.env` and also starts uvicorn with reload. Both commands behave the same by default since `.env.example` sets `PORT=8000`.

## 5. Run tests

From `task-tracker/backend`, with the virtual environment active:

```bash
pytest -v
```

For a single test:

```bash
pytest tests/test_tasks.py::test_name -v
```

The suite (42 tests as of this writing) covers task CRUD, title/due-date validation, overdue computation, status-transition rules, comment endpoints (add, blank-rejection, list, delete, 404 handling), and a CORS preflight check.

## 6. Run with Docker

Run from the repo root.

```bash
cd task-tracker
docker build -t task-tracker-api .
docker run --rm -p 8000:8000 task-tracker-api
```

The server is then reachable the same way as local runs:

```bash
curl http://127.0.0.1:8000/health
```

Notes on the image (from `task-tracker/Dockerfile`):

- Multi-stage build: dependencies are installed in a `builder` stage, then only the installed packages, `backend/app`, and `frontend` are copied into the `runtime` stage — no `requirements.txt`, tests, docs, or `.env` end up in the final image.
- Runs as a non-root user (`app`, uid 1000).
- The container's `CMD` starts uvicorn directly on `0.0.0.0:8000` with no `--reload`; it does **not** go through `app.main`'s `__main__` block, so the `PORT` value from `.env` has no effect inside the container — `.env` isn't copied into the image at all, and the port is hardcoded to `8000` in the Dockerfile.

## 7. CI workflow summary

Defined in [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), job `test`:

- **Triggers**: every `push` and every `pull_request` (no branch filter).
- **Runner**: `ubuntu-latest`, working directory `task-tracker/backend`.
- **Steps**: checkout → set up Python 3.11 → `pip install -r requirements.txt` → `pytest -v`.

The workflow only runs the test suite — it does not build/push the Docker image, run linting, or deploy anywhere.

## 8. Project structure

```text
task-tracker/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app + task, comment, and health routes
│   │   ├── models.py          # Task/Comment models, enums, overdue helper
│   │   ├── business_rules.py  # Status-transition allow-list
│   │   ├── schemas.py         # Health-check response schema
│   │   ├── storage.py         # In-memory task and comment store
│   │   └── routes.py          # Unused/vestigial empty APIRouter (not imported by main.py)
│   │
│   ├── tests/                 # pytest suite (task, due-date, comment, CORS coverage)
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/
│   └── index.html              # Single-file Kanban board (talks to the backend)
│
├── docs/
│   └── midcourse/               # User stories, decision note, prompt log, reflection
│
├── Dockerfile
├── .dockerignore
├── .gitignore
└── README.md

.github/
└── workflows/
    └── ci.yml                   # Test-only CI pipeline (see Section 7)
```

## 9. Project conventions and current limitations

- **In-memory only, nothing persisted.** All task/comment data lives in module-level dicts in `app/storage.py` for the life of the process; a restart clears everything. The FastAPI app's `description` field still mentions JSON file storage — that's stale text, not actual behavior (see [`docs/midcourse/mini-adr.md`](docs/midcourse/mini-adr.md)).
- **Comments do not cascade-delete with their task.** Comments are a separate top-level store keyed by `task_id`, not nested under tasks. Deleting a task (`storage.delete_task`) only removes the task itself — comments referencing that task are left behind (orphaned). Earlier project docs describe cascade delete as intended behavior; that has not been implemented.
- **Status transitions are an explicit allow-list, not a general state machine.** Only forward moves and same-status no-ops are permitted (`app/business_rules.py`); e.g. `ToDo -> Done` directly is rejected with `422`.
- **`app/routes.py` is unused.** It defines an empty `APIRouter` left over from an earlier stage of the project; it is never imported or included by `app/main.py`.
- **CORS is wide open** (`allow_origins=["*"]`, all methods/headers) — fine for local development, not appropriate as-is for any public deployment.
- **Single-process, in-memory state.** The task/comment stores are plain process-global dicts with no locking — state is not shared or synchronized across multiple workers, processes, or replicas.
- **No authentication, no database, no deployment/production configuration.** This is a learning project; none of those concerns are implemented, and nothing in this repo should be treated as production-ready.

## 10. Technical notes / decisions

No `docs/decisions/` directory exists in this repo. [VERIFY: confirm whether one is expected for this module.] The closest existing technical note is the mid-course decision record:

- [`docs/midcourse/mini-adr.md`](docs/midcourse/mini-adr.md) — decision note on the due-date/overdue feature and task comments, including alternatives considered and rejected.

Related docs under `docs/midcourse/`: `user-stories.md`, `prompt-log.md`, `reflection.md`, `verification.md`.

## Final Project

Branch reviewed: final-project

### What this submission demonstrates
- Existing Task Tracker app still runs inside the intended course scope.
- CI runs the pytest suite on push and/or pull request.
- Docker image builds and runs with /health returning 200.
- AI review, security, and ownership evidence is in docs/.

### How to run locally

```bash
cd task-tracker/backend
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env         # `cp` on macOS/Linux
python -m app.main
```

### How to run tests

```bash
pytest -v
```

### How to run with Docker

```bash
docker build -t task-tracker-api .
docker run --rm -p 8000:8000 task-tracker-api
curl http://127.0.0.1:8000/health
```

### Evidence files
- docs/release-evidence.md
- docs/final-ai-review.md
- docs/ai-playbook.md

### AI assistance summary
AI helped draft or review: the CI workflow audit, the Dockerfile/.dockerignore safety review, README claim verification, and docs/release-evidence.md.
I verified the work by: actually running the app (`python -m app.main`) and curling `/health`, running the full pytest suite, and building and running the Docker image and curling its `/health` endpoint — not by trusting the docs or AI output at face value.
One AI suggestion I rejected or corrected: TODO-USER