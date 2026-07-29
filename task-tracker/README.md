# Task Tracker

A learning-project REST API for tracking tasks, built with Python, FastAPI, and Pydantic, with a single-page Kanban frontend.

Task data is held in an in-memory store during the server's lifetime. The persistence approach and its reasoning are recorded in ADR-001: Use JSON File Storage for Task Persistence.

This repository contains the mid-course project: full task CRUD plus two added features — optional **due dates with a server-computed overdue flag**, and **task comments** (list, add, delete).

## Project structure

```text
task-tracker/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app + task, comment, and health routes
│   │   ├── models.py        # Task/Comment models, enums, overdue helper
│   │   ├── schemas.py       # Health-check response schema
│   │   ├── storage.py       # In-memory task and comment store
│   │   └── routes.py        # Task router seam
│   │
│   ├── tests/               # pytest suite (task, due-date, comment coverage)
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   └── index.html           # Single-file Kanban board (talks to the backend)
│
├── docs/
│   └── midcourse/           # User stories, decision note, prompt log
│
├── .gitignore
└── README.md
```

## Requirements

Python 3.10 or newer (the type hints use the `list[dict]` / `X | None` syntax from 3.10+).

Check your version:

```bash
python --version
```

## Setup

All commands below are run from the `backend/` directory.

```bash
cd task-tracker/backend
```

**1. Create a virtual environment**

```bash
python -m venv venv
```

**2. Activate it**

macOS / Linux:

```bash
source venv/bin/activate
```

Windows (PowerShell):

```powershell
venv\Scripts\Activate.ps1
```

Your shell prompt should now be prefixed with `(venv)`.

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Create your local `.env`**

```bash
cp .env.example .env
```

On Windows use `copy .env.example .env`. The `.env` file is git-ignored; `.env.example` is the committed reference.

## Running the backend

From `backend/`, with the virtual environment active:

```bash
python -m app.main
```

This loads `APP_ENV` and `PORT` from `.env` (via python-dotenv) and starts uvicorn with reload enabled. With the default `.env`, the server starts at http://127.0.0.1:8000. Change `PORT` in `.env` to use a different port.

Interactive API docs are generated automatically:

- Swagger UI — http://127.0.0.1:8000/docs
- ReDoc — http://127.0.0.1:8000/redoc

## Opening the frontend

The frontend is a single static file at `frontend/index.html`. With the backend running, open it either way:

- The backend serves it directly at http://127.0.0.1:8000/ — just open that URL.
- Or open `frontend/index.html` in your browser directly (double-click, or `start frontend/index.html` on Windows / `open frontend/index.html` on macOS).

The page talks to the backend at `http://127.0.0.1:8000`, so the backend must be running first. Create a task, then click **Edit** on a card to set a due date or add comments. Use the **Show overdue only** toggle to filter the board.

## Running tests

From `backend/`, with the virtual environment active:

```bash
pytest
```

For per-test output:

```bash
pytest -v
```

The suite covers task CRUD, due-date validation and overdue computation, and the comment endpoints (add, blank-rejection, list, delete, and 404 handling).

## Features

**Due dates & overdue.** Tasks accept an optional ISO 8601 `due_date`, normalized to UTC. `overdue` is computed on the backend as a read-only field — true when the due date is in the past and the task isn't `Done` — and the same logic backs the `?overdue=true|false` list filter.

**Task comments.** Each task has comments with list, add, and delete endpoints. Blank text is rejected with a `422`; missing tasks or comments return `404`; deleting a task cascades to remove its comments.

## Health check

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