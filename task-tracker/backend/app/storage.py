from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models import (
    Comment,
    CommentCreate,
    TaskCreate,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
    is_task_overdue,
)

_tasks: dict[str, TaskResponse] = {}
_comments: dict[str, Comment] = {}

def add_task(payload: TaskCreate) -> TaskResponse:
    """Create and store a new task.

    Args:
        payload: Validated task-creation data.

    Returns:
        TaskResponse: The newly stored task, with a generated UUID `id` and
        `created_at`/`updated_at` both set to the current UTC time.
    """
    now = datetime.now(timezone.utc)
    task = TaskResponse(
        id=str(uuid4()),
        title=payload.title,
        description=payload.description or "",
        status=payload.status,
        priority=payload.priority,
        assignee=payload.assignee,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    _tasks[task.id] = task
    return task


def get_all_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    overdue: Optional[bool] = None,
) -> list[TaskResponse]:
    """Return stored tasks, optionally filtered by status, priority, and/or overdue state.

    Args:
        status: If given, only tasks with this status are included.
        priority: If given, only tasks with this priority are included.
        overdue: If given, only tasks whose `is_task_overdue()` result
            matches are included.

    Returns:
        list[TaskResponse]: Tasks matching all provided filters (AND
        semantics). Order follows insertion order of the underlying store.
    """
    tasks = list(_tasks.values())
    if status is not None:
        tasks = [task for task in tasks if task.status == status]
    if priority is not None:
        tasks = [task for task in tasks if task.priority == priority]
    if overdue is not None:
        tasks = [task for task in tasks if is_task_overdue(task) is overdue]
    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    """Look up a task by id.

    Args:
        task_id: UUID string of the task.

    Returns:
        Optional[TaskResponse]: The task, or None if no task with that id
        exists.
    """
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
    """Apply a partial update to a stored task.

    Only fields explicitly set on `payload` are applied
    (`model_dump(exclude_unset=True)`); fields omitted from the request are
    left unchanged.

    Args:
        task_id: UUID string of the task to update.
        payload: Fields to update.

    Returns:
        Optional[TaskResponse]: None if no task with `task_id` exists. If
        `payload` has no explicitly set fields, the existing task is
        returned unchanged (and `updated_at` is not touched). Otherwise the
        updated task is returned with `updated_at` set to the current UTC
        time.
    """
    task = _tasks.get(task_id)
    if task is None:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return task

    updated = task.model_copy(
        update={**updates, "updated_at": datetime.now(timezone.utc)}
    )
    _tasks[task_id] = updated
    return updated


def delete_task(task_id: str) -> bool:
    """Delete a task by id.

    Only removes the task from the `_tasks` store; comments belonging to
    the task in `_comments` are left behind (orphaned). This is a known
    discrepancy from the README's documented cascade-delete behavior.

    Args:
        task_id: UUID string of the task to delete.

    Returns:
        bool: True if a task was deleted, False if no task with `task_id`
        existed.
    """
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def get_comments_for_task(task_id: str) -> list[Comment]:
    """Return all comments for a task, oldest first.

    Args:
        task_id: UUID string of the parent task. Not validated against the
            task store here — callers are expected to confirm the task
            exists first.

    Returns:
        list[Comment]: Comments whose `task_id` matches, sorted by
        `created_at` ascending. Empty list if none exist.
    """
    result = [c for c in _comments.values() if c.task_id == task_id]
    result.sort(key=lambda c: c.created_at)
    return result


def add_comment(task_id: str, payload: CommentCreate) -> Comment:
    """Create and store a new comment on a task.

    [VERIFY] Does not check that `task_id` refers to an existing task;
    callers (the route handlers in main.py) are expected to validate this
    first via `_require_task`.

    Args:
        task_id: UUID string of the parent task.
        payload: Validated comment-creation data.

    Returns:
        Comment: The newly stored comment, with a generated UUID `id` and
        `created_at` set to the current UTC time.
    """
    comment = Comment(
        id=str(uuid4()),
        task_id=task_id,
        text=payload.text,
        created_at=datetime.now(timezone.utc),
    )
    _comments[comment.id] = comment
    return comment


def get_comment_by_id(comment_id: str) -> Optional[Comment]:
    """Look up a comment by id.

    Args:
        comment_id: UUID string of the comment.

    Returns:
        Optional[Comment]: The comment, or None if no comment with that id
        exists.
    """
    return _comments.get(comment_id)


def delete_comment(comment_id: str) -> bool:
    """Delete a comment by id.

    Args:
        comment_id: UUID string of the comment to delete.

    Returns:
        bool: True if a comment was deleted, False if no comment with
        `comment_id` existed.
    """
    if comment_id not in _comments:
        return False
    del _comments[comment_id]
    return True


def _reset() -> None:
    _tasks.clear()
    _comments.clear()