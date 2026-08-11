# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Task Tracker: a learning-project REST API built with Python, FastAPI, and Pydantic, plus a single-file Kanban frontend. Task and comment data live in an in-memory Python dict for the server's lifetime — nothing is persisted to disk or a database (see `task-tracker/docs/midcourse/mini-adr.md` for the reasoning, despite the API description's mention of JSON file storage, which is aspirational/stale).

The actual project root is `task-tracker/` (this repo's top level is a thin wrapper around it).

## Commands

All commands run from `task-tracker/backend/` with the virtualenv active.

```bash
cd task-tracker/backend
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
copy .env.example .env         # `cp` on macOS/Linux
```

Run the server (loads `APP_ENV`/`PORT` from `.env`, starts uvicorn with reload on `http://127.0.0.1:8000`):

```bash
python -m app.main
```

Run tests:

```bash
pytest
pytest -v                                    # per-test output
pytest tests/test_tasks.py::test_name -v     # single test
```

The frontend is a static file with no build step: open `task-tracker/frontend/index.html` directly, or load it from the running backend at `http://127.0.0.1:8000/` (served via `FileResponse` in `main.py`). It talks to the API at a hardcoded `http://127.0.0.1:8000`, so the backend must be running.

## Architecture

- **`app/models.py`** — All Pydantic models and enums (`TaskStatus`, `TaskPriority`, `TaskCreate`/`TaskUpdate`/`TaskResponse`, `Comment`/`CommentCreate`), plus the `is_task_overdue()` helper. `TaskBase` centralizes `due_date` parsing (ISO 8601 → UTC-normalized `datetime`, `Z` suffix handled) and JSON serialization via a shared `field_validator`/`field_serializer` pair inherited by both create and update schemas. `overdue` on `TaskResponse` is a `computed_field`, not a stored value — it's derived at read time so it can never go stale.
- **`app/storage.py`** — The entire persistence layer: two module-level dicts (`_tasks`, `_comments`) keyed by UUID. All reads/writes go through this module's functions (`add_task`, `get_all_tasks`, `update_task`, `add_comment`, etc.) rather than touching the dicts directly. `_reset()` clears both dicts and is called by the `_reset_storage` autouse fixture in `tests/conftest.py` before/after every test — the suite depends on this for isolation since state is process-global.
- **`app/business_rules.py`** — Task status transition validation as an explicit allow-list (`VALID_TRANSITIONS`), not a general state machine. Only forward moves and same-status no-ops are permitted (e.g. `ToDo -> Done` directly is rejected with 422); this is enforced in `main.py` before `storage.update_task` is called, using the task's *current* stored status.
- **`app/main.py`** — All route handlers live directly in this file (task CRUD, comment CRUD, `/health`, frontend serving). **`app/routes.py` is an unused/vestigial empty `APIRouter` left over from an earlier module of the course** — it is never imported or included by `main.py`; don't assume routes live there.
- **`app/schemas.py`** — Only `HealthResponse` lives here; task/comment schemas are in `models.py` despite the module docstring's stale "will be added in a later module" note.

### Request flow

`main.py` handler → validates via Pydantic model (`TaskCreate`/`TaskUpdate`/`CommentCreate`) → for status changes, `business_rules.validate_status_transition()` checks the transition against the existing stored task → `storage.py` function performs the in-memory mutation and returns a fresh model instance → FastAPI serializes the `response_model`.

`_require_task()` in `main.py` is the shared 404 helper — call it any time an endpoint needs to assert a task exists before proceeding (comment endpoints do this to get task-scoped 404s).

### Overdue computation

`overdue` is never stored — it's computed identically in two places from one source of truth, `is_task_overdue()` in `models.py`: once as `TaskResponse.overdue` (per-task computed field) and once inside `storage.get_all_tasks()` for the `?overdue=true|false` query filter. If you change overdue semantics, change only the helper; the two call sites will pick it up automatically. A task is overdue iff `due_date` is set, is in the past relative to server UTC time, and `status != Done`.

### Comments

Comments are a separate top-level store (`_comments`), not nested inside tasks, each holding its own `task_id` foreign key. **Known discrepancy:** the README documents cascade delete ("deleting a task cascades to remove its comments"), but `storage.delete_task()` currently only removes from `_tasks` and never touches `_comments` — orphaned comments are left behind. If asked to fix or touch task deletion, this is the place to reconcile behavior with the documented contract.

### Testing conventions

- `tests/conftest.py` provides `client` (a `TestClient`) and `created_task` (a task pre-created via the API) fixtures, plus the autouse storage reset.
- Tests hit the API through `TestClient`/HTTP, not by calling `storage.py` functions directly — follow this pattern for new tests so they exercise validation and routing too.
- `tests/verify_a.py` is a standalone manual verification script (run directly with `python`, not collected by pytest) using `expect_fail`/`expect_ok` helpers against Pydantic models directly — a different style from the pytest suite, kept for its own ad hoc model-validation checks.
