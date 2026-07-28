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
    tasks = list(_tasks.values())
    if status is not None:
        tasks = [task for task in tasks if task.status == status]
    if priority is not None:
        tasks = [task for task in tasks if task.priority == priority]
    if overdue is not None:
        tasks = [task for task in tasks if is_task_overdue(task) is overdue]
    return tasks


def get_task_by_id(task_id: str) -> Optional[TaskResponse]:
    return _tasks.get(task_id)


def update_task(task_id: str, payload: TaskUpdate) -> Optional[TaskResponse]:
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
    if task_id not in _tasks:
        return False
    del _tasks[task_id]
    return True


def get_comments_for_task(task_id: str) -> list[Comment]:
    result = [c for c in _comments.values() if c.task_id == task_id]
    result.sort(key=lambda c: c.created_at)
    return result


def add_comment(task_id: str, payload: CommentCreate) -> Comment:
    comment = Comment(
        id=str(uuid4()),
        task_id=task_id,
        text=payload.text,
        created_at=datetime.now(timezone.utc),
    )
    _comments[comment.id] = comment
    return comment


def get_comment_by_id(comment_id: str) -> Optional[Comment]:
    return _comments.get(comment_id)


def delete_comment(comment_id: str) -> bool:
    if comment_id not in _comments:
        return False
    del _comments[comment_id]
    return True


def _reset() -> None:
    _tasks.clear()
    _comments.clear()