from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_serializer, field_validator

class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_date: Optional[datetime] = None

    @field_validator("due_date", mode="before")
    @classmethod
    def validate_due_date(cls, value: Optional[object]) -> Optional[datetime]:
        """Parse and normalize `due_date` before Pydantic's type validation.

        Accepts `None`, a `datetime`, or an ISO 8601 string (a trailing `Z`
        is treated as `+00:00`). Naive datetimes/strings are assumed to be
        UTC; timezone-aware ones are converted to UTC.

        Args:
            value: The raw input for `due_date`.

        Returns:
            Optional[datetime]: `None`, or a UTC-aware `datetime`.

        Raises:
            ValueError: If `value` is an empty/blank string, a string that
                cannot be parsed as ISO 8601, or a type other than `None`,
                `datetime`, or `str`.
        """
        if value is None:
            return None

        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("due_date must be a valid ISO 8601 date or datetime")
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(raw)
            except ValueError as exc:
                raise ValueError("due_date must be a valid ISO 8601 date or datetime") from exc
        else:
            raise ValueError("due_date must be a valid ISO 8601 date or datetime")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        return dt

    @field_serializer("due_date", when_used="json")
    def serialize_due_date(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize `due_date` to an ISO 8601 string for JSON output.

        Args:
            value: The stored `due_date`.

        Returns:
            Optional[str]: `None`, or `value.isoformat()`.
        """
        if value is None:
            return None
        return value.isoformat()


class TaskCreate(TaskBase):
    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        """Strip and validate the task title.

        Args:
            value: The raw title.

        Returns:
            str: The stripped title.

        Raises:
            ValueError: If the stripped title is blank or exceeds 200
                characters.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        if len(stripped) > 200:
            raise ValueError("title must not exceed 200 characters")
        return stripped


class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: Optional[str]) -> Optional[str]:
        """Strip and validate the task title, if provided.

        Args:
            value: The raw title, or None if `title` was omitted from the
                update payload.

        Returns:
            Optional[str]: None if `value` is None; otherwise the stripped
            title.

        Raises:
            ValueError: If `value` is provided but the stripped title is
                blank or exceeds 200 characters.
        """
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title must not be blank")
        if len(stripped) > 200:
            raise ValueError("title must not exceed 200 characters")
        return stripped


class TaskResponse(TaskBase):
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    created_at: datetime
    updated_at: datetime

    @computed_field(return_type=bool)
    @property
    def overdue(self) -> bool:
        """Whether this task is currently overdue.

        Computed at read time (not stored) via `is_task_overdue()`, so it
        can never go stale relative to `due_date`/`status`.

        Returns:
            bool: True if `due_date` is set, is in the past relative to the
            current UTC time, and `status` is not Done.
        """
        return is_task_overdue(self)

class Comment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    task_id: str
    text: str
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize `created_at` to an ISO 8601 string for JSON output.

        Args:
            value: The stored `created_at` timestamp.

        Returns:
            str: `value.isoformat()`.
        """
        return value.isoformat()


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        """Strip and validate comment text.

        Args:
            value: The raw comment text.

        Returns:
            str: The stripped text.

        Raises:
            ValueError: If the stripped text is blank or exceeds 2000
                characters.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        if len(stripped) > 2000:
            raise ValueError("text must not exceed 2000 characters")
        return stripped



def is_task_overdue(task: TaskResponse | TaskCreate | TaskUpdate, now: Optional[datetime] = None) -> bool:
    """Compute whether a task counts as overdue.

    Single source of truth for overdue semantics, used by both
    `TaskResponse.overdue` and the `?overdue=` filter in
    `storage.get_all_tasks()`.

    Args:
        task: A task-like object read for its `due_date` and `status`
            attributes. [VERIFY] The type hint includes `TaskCreate` and
            `TaskUpdate`, but in this codebase the function is only called
            with `TaskResponse` instances; `TaskUpdate.status` can be
            `None` (unset), in which case the `status == TaskStatus.DONE`
            check below is simply False rather than raising.
        now: Reference time to compare `due_date` against. Falls back to
            the current UTC time if not given (or falsy).

    Returns:
        bool: False if `due_date` is None or `status` is Done; otherwise
        True if `due_date` is earlier than the reference time.
    """
    if getattr(task, "due_date", None) is None:
        return False
    if getattr(task, "status", None) == TaskStatus.DONE:
        return False

    reference_time = now or datetime.now(timezone.utc)
    return task.due_date < reference_time
def _reset() -> None:
    _tasks.clear()
    _comments.clear()