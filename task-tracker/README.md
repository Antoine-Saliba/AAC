Task Tracker

A learning-project REST API for tracking tasks, built with Python, FastAPI, and Pydantic.

Task data is persisted to a local JSON file rather than a database. That choice, along with the reasoning behind it, is recorded in ADR-001: Use JSON File Storage for Task Persistence.

This repository currently contains the Module 1 skeleton: the FastAPI application instance and a health-check endpoint. Task CRUD endpoints are not implemented yet.

Project structure
text
task-tracker/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app instance + /health endpoint
│   │   ├── models.py        # Domain enums (status, priority)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── storage.py       # JSON file read/write layer
│   │   └── routes.py        # Task router (empty until a later module)
│   │
│   ├── data/
│   │   └── tasks.json       # Local persistence file
│   │
│   ├── .env.example
│   └── requirements.txt
│
├── .gitignore
└── README.md

The frontend/ directory from ADR-001 is not part of this skeleton and will be added in a later module.

Requirements
Python 3.10 or newer (the type hints in storage.py use the list[dict] syntax introduced in 3.9, and the project is tested on 3.10+)

Check your version:

bash
python3 --version
Setup

All commands below are run from the backend/ directory.

bash
cd task-tracker/backend

1. Create a virtual environment

bash
python3 -m venv venv

2. Activate it

macOS / Linux:

bash
source venv/bin/activate

Windows (PowerShell):

powershell
venv\Scripts\Activate.ps1

Your shell prompt should now be prefixed with (venv).

3. Install dependencies

bash
pip install -r requirements.txt

4. Create your local .env

bash
cp .env.example .env

On Windows use copy .env.example .env. The .env file is git-ignored; .env.example is the committed reference.

Verify your version pins. requirements.txt ships with pinned versions that were current when the file was written. After installing, run pip freeze and update requirements.txt to match what actually resolved in your environment. This keeps the pins honest and reproducible.

Running the server

From backend/, with the virtual environment active:

bash
python -m app.main

This loads APP_ENV and PORT from .env (via python-dotenv) and starts uvicorn with reload enabled.
--reload restarts the server automatically when you edit a file. Use it in development only.

With the default .env, the server starts at http://127.0.0.1:8000. Change PORT in .env to use a different port.

Testing the health endpoint

With the server running, in a second terminal:

bash
curl http://127.0.0.1:8000/health

Expected response, HTTP 200:

json
{
  "status": "ok",
  "timestamp": "2026-07-23T10:15:30.123456+00:00"
}

To see the status code and headers alongside the body:

bash
curl -i http://127.0.0.1:8000/health
Interactive API documentation

FastAPI generates interactive docs from your route definitions and Pydantic schemas. With the server running, open either in a browser:

Swagger UI — http://127.0.0.1:8000/docs
ReDoc — http://127.0.0.1:8000/redoc

In Swagger UI you can expand GET /health, click Try it out, then Execute to call the endpoint without leaving the browser. The raw OpenAPI schema is at http://127.0.0.1:8000/openapi.json.

Scope of this module

Deliberately not included at this stage:

Task CRUD endpoints
Authentication or user accounts
A database implementation
Docker or cloud deployment
Frontend files
Notifications or real-time updates

routes.py and models.py exist as the seams these features will grow into, keeping the structure aligned with ADR-001 from the start.



## Running the app

### Backend

From `backend/`, with the virtual environment active:

```bash
python -m app.main
```

The server starts at http://127.0.0.1:8000 (change `PORT` in `.env` to use a
different port). Interactive API docs are at http://127.0.0.1:8000/docs.

### Frontend

The frontend is a single static file at `frontend/index.html`. With the backend
running, open it one of two ways:

- The backend serves it directly at http://127.0.0.1:8000/ — just open that URL.
- Or open `frontend/index.html` in your browser directly (double-click, or
  `open frontend/index.html` on macOS / `start frontend/index.html` on Windows).

The page talks to the backend at `http://127.0.0.1:8000`, so the backend must be
running first. Create a task, then click **Edit** on a card to add due dates and
comments.

### Running tests

From `backend/`, with the virtual environment active:

```bash
pytest
```

To see per-test output and which cases ran:

```bash
pytest -v
```