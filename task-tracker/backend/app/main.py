"""Task Tracker API - application entry point.

Module 1 skeleton: creates the FastAPI application instance and exposes a
single /health endpoint. CRUD endpoints are intentionally not implemented yet.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app import storage
from app.business_rules import validate_status_transition
from app.models import Comment, CommentCreate, TaskCreate, TaskPriority, TaskResponse, TaskStatus, TaskUpdate
from app.schemas import HealthResponse

# Load environment variables from a local .env file if one is present.
load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI(
    title="Task Tracker API",
    description=(
        "A learning-project REST API for tracking tasks. "
        "Persistence is backed by a local JSON file (see ADR-001)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).resolve().parent.parent.parent / "frontend" / "index.html"


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """Serve the Kanban frontend's static HTML file.

    Route: GET /

    Hidden from the OpenAPI schema (`include_in_schema=False`) since it
    serves a static asset rather than an API resource.

    Returns:
        FileResponse: The contents of frontend/index.html.
    """
    return FileResponse(FRONTEND_PATH)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Liveness probe.

    Route: GET /health

    Returns:
        HealthResponse: HTTP 200 with `status="ok"` and the current UTC
        timestamp in ISO 8601 format.
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
def _require_task(task_id: str) -> TaskResponse:
    task = storage.get_task_by_id(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task with id {task_id} not found")
    return task

@app.get("/tasks", response_model=list[TaskResponse], tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    overdue: bool | None = None,
) -> list[TaskResponse]:
    """List tasks, optionally filtered by status, priority, and/or overdue state.

    Route: GET /tasks

    Args:
        status: If given, only tasks with this status are included.
        priority: If given, only tasks with this priority are included.
        overdue: If given, only tasks whose computed overdue state (see
            `is_task_overdue` in app.models) matches are included.

    Returns:
        list[TaskResponse]: Tasks matching all provided filters (filters are
        combined with AND semantics).
    """
    return storage.get_all_tasks(status=status, priority=priority, overdue=overdue)


@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def get_task(task_id: str) -> TaskResponse:
    """Fetch a single task by id.

    Route: GET /tasks/{task_id}

    Args:
        task_id: UUID string of the task to fetch.

    Returns:
        TaskResponse: The matching task.

    Raises:
        HTTPException: 404 if no task with `task_id` exists.
    """
    return _require_task(task_id)


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED, tags=["tasks"])
def create_task(payload: TaskCreate) -> TaskResponse:
    """Create a new task.

    Route: POST /tasks

    Args:
        payload: Task fields to create; validated by `TaskCreate` (see
            app.models for field-level validation rules).

    Returns:
        TaskResponse: The newly created task, HTTP 201.
    """
    return storage.add_task(payload)


@app.patch("/tasks/{task_id}", response_model=TaskResponse, tags=["tasks"])
def update_task(task_id: str, payload: TaskUpdate) -> TaskResponse:
    """Partially update a task.

    Route: PATCH /tasks/{task_id}

    Only fields explicitly set on `payload` are applied; omitted fields are
    left unchanged (`storage.update_task` uses `exclude_unset=True`). If
    `payload.status` is set, the transition from the task's current stored
    status to the new status is validated against
    `business_rules.VALID_TRANSITIONS` before the update is applied.

    Args:
        task_id: UUID string of the task to update.
        payload: Fields to update; validated by `TaskUpdate`.

    Returns:
        TaskResponse: The updated task.

    Raises:
        HTTPException: 404 if no task with `task_id` exists.
        HTTPException: 422 if `payload.status` is set and the transition
            from the task's current status is not in the allowed set.
    """
    if payload.status is not None:
        existing = _require_task(task_id)
        validate_status_transition(existing.status, payload.status)

    task = storage.update_task(task_id, payload)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["tasks"])
def delete_task(task_id: str) -> None:
    """Delete a task.

    Route: DELETE /tasks/{task_id}

    Known discrepancy: this does not remove the task's comments from the
    separate `_comments` store, despite the README documenting cascade
    delete (see docs/midcourse/mini-adr.md and storage.delete_task).

    Args:
        task_id: UUID string of the task to delete.

    Returns:
        None: HTTP 204 on success.

    Raises:
        HTTPException: 404 if no task with `task_id` exists.
    """
    if not storage.delete_task(task_id):
        raise HTTPException(
            status_code=404,
            detail=f"Task with id {task_id} not found",
        )




@app.get(
    "/tasks/{task_id}/comments",
    response_model=list[Comment],
    tags=["comments"],
)
def list_comments(task_id: str) -> list[Comment]:
    """List all comments on a task, oldest first.

    Route: GET /tasks/{task_id}/comments

    Args:
        task_id: UUID string of the parent task.

    Returns:
        list[Comment]: Comments for the task, sorted by `created_at`
        ascending.

    Raises:
        HTTPException: 404 if no task with `task_id` exists.
    """
    _require_task(task_id)
    return storage.get_comments_for_task(task_id)


@app.post(
    "/tasks/{task_id}/comments",
    response_model=Comment,
    status_code=status.HTTP_201_CREATED,
    tags=["comments"],
)
def create_comment(task_id: str, payload: CommentCreate) -> Comment:
    """Add a comment to a task.

    Route: POST /tasks/{task_id}/comments

    Args:
        task_id: UUID string of the parent task.
        payload: Comment text to create; validated by `CommentCreate`.

    Returns:
        Comment: The newly created comment, HTTP 201.

    Raises:
        HTTPException: 404 if no task with `task_id` exists.
    """
    _require_task(task_id)
    return storage.add_comment(task_id, payload)


@app.delete(
    "/tasks/{task_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["comments"],
)
def delete_comment(task_id: str, comment_id: str) -> None:
    """Delete a comment from a task.

    Route: DELETE /tasks/{task_id}/comments/{comment_id}

    Args:
        task_id: UUID string of the parent task.
        comment_id: UUID string of the comment to delete.

    Returns:
        None: HTTP 204 on success.

    Raises:
        HTTPException: 404 if `task_id` does not exist, or if `comment_id`
            does not exist or does not belong to `task_id`.
    """
    _require_task(task_id)
    comment = storage.get_comment_by_id(comment_id)
    if comment is None or comment.task_id != task_id:
        raise HTTPException(
            status_code=404,
            detail=f"Comment with id {comment_id} not found",
        )
    storage.delete_comment(comment_id)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=PORT, reload=True)
