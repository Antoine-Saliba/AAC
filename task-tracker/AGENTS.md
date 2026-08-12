# AGENTS.md — Task Tracker / AI-Assisted Coding Module 5

## Project summary

Task Tracker is a learning-project REST API with a static Kanban frontend.

- Backend: Python, FastAPI, and Pydantic.
- Frontend: one static HTML/CSS/JavaScript file; no frontend build system is visible.
- Storage: process-local in-memory dictionaries. Tasks and comments are lost when the server restarts.
- The backend serves the frontend from `GET /`; the frontend calls `http://127.0.0.1:8000`.

Sources: `README.md`, `backend/app/main.py`, `backend/app/storage.py`, and `frontend/index.html`.

## Module 5 guardrails

This repository is being used for AI-Assisted Coding Module 5: grading and governance, not feature development.

- Work read-only by default.
- Prefer documentation work first. Edit only `docs/` unless the user explicitly authorizes another path.
- Do not modify `backend/app/` unless the user explicitly approves one specific minimal fix.
- Keep one bounded task per Codex task/thread. Do not combine unrelated review, implementation, and documentation work.
- Before making a repository claim, inspect and cite the relevant file(s). If a fact is not visible, write **not confirmed** rather than inferring it.
- When an edit is requested, describe the target, scope, and verification before editing. Preserve unrelated user changes.

## Supported commands

Run backend commands from `backend/`.

```powershell
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python -m app.main
pytest -v
```

The documented alternative server command is:

```powershell
uvicorn app.main:app --reload --port 8000
```

The app runs on `http://127.0.0.1:8000` by default. API documentation is available at `/docs` and `/redoc`.

Docker commands documented by the repository, run from this project directory:

```powershell
docker build -t task-tracker-api .
docker run --rm -p 8000:8000 task-tracker-api
```

`pytest -v` is also the command executed by CI with Python 3.11. No lint, formatter, type-check, frontend test, or deployment command is visible; those are **not confirmed**.

Sources: `README.md`, `backend/app/main.py`, `backend/requirements.txt`, `Dockerfile`, and `.github/workflows/ci.yml`.

## Visible business rules

### Tasks

- Status values: `ToDo`, `InProgress`, `Done`.
- Priority values: `Low`, `Medium`, `High`.
- New-task defaults: status `ToDo`, priority `Medium`, and description `""`.
- A task title is required, trimmed, cannot be blank, and cannot exceed 200 characters.
- Task request schemas reject unknown fields.
- `PATCH` updates only supplied fields; an empty patch succeeds without changing the task.
- `due_date` accepts `null`, ISO 8601 date/datetime strings, or Python datetimes. Naive values are treated as UTC; timezone-aware values are normalized to UTC.
- `overdue` is read-only/computed: a task is overdue only when it has a past due date and is not `Done`.
- List filtering supports `status`, `priority`, and `overdue`.

Allowed status transitions are an explicit allow-list:

| Current | Allowed next status |
| --- | --- |
| `ToDo` | `ToDo`, `InProgress` |
| `InProgress` | `InProgress`, `Done` |
| `Done` | `Done`, `InProgress` |

A direct `ToDo` → `Done` update returns HTTP 422.

Sources: `backend/app/models.py`, `backend/app/business_rules.py`, `backend/app/main.py`, `backend/app/storage.py`, and `backend/tests/test_tasks.py`.

### Comments and storage

- Comment text is trimmed, cannot be blank, and cannot exceed 2,000 characters.
- Comment request schemas reject unknown fields.
- Comments belong to a task and list in ascending `created_at` order.
- Task and comment data are stored in separate in-memory dictionaries.
- Deleting a task does not delete its comments; existing comments can become orphaned.

Sources: `backend/app/models.py`, `backend/app/main.py`, `backend/app/storage.py`, and `backend/tests/test_tasks.py`.

## Security and governance

- Never paste, log, commit, or expose secrets, credentials, tokens, or local `.env` contents. Use `.env.example` only as a non-secret reference.
- Do not run destructive commands or overwrite/delete files unless the user explicitly authorizes the precise target and scope.
- Use read-only inspection before proposing changes. Cite the file(s) inspected for all repository findings.
- Do not claim that tests, CI, security controls, deployment behavior, or requirements exist unless visible in inspected repository files.
- Do not invent findings, evidence, or content for the “AI-Assisted Coding - Module 5 Prompt Library.” If it is not visible in the repository or provided by the user, mark it **not confirmed**.
- Do not treat the application as production-ready: authentication, a database, and production deployment configuration are not visible.

## Test conventions

Tests use FastAPI `TestClient`. An autouse fixture clears in-memory storage before and after each test. Keep any approved test work at the HTTP/API boundary unless the user directs otherwise. `tests/verify_a.py` is a standalone model-verification script and is not confirmed as part of pytest collection.

Sources: `backend/tests/conftest.py`, `backend/tests/test_tasks.py`, `backend/tests/verify_a.py`, and `backend/pytest.ini`.
