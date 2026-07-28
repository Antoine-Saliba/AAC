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
        return is_task_overdue(self)

class Comment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    task_id: str
    text: str
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def serialize_created_at(self, value: datetime) -> str:
        return value.isoformat()


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("text must not be blank")
        if len(stripped) > 2000:
            raise ValueError("text must not exceed 2000 characters")
        return stripped



def is_task_overdue(task: TaskResponse | TaskCreate | TaskUpdate, now: Optional[datetime] = None) -> bool:
    if getattr(task, "due_date", None) is None:
        return False
    if getattr(task, "status", None) == TaskStatus.DONE:
        return False

    reference_time = now or datetime.now(timezone.utc)
    return task.due_date < reference_time
def _reset() -> None:
    _tasks.clear()
    _comments.clear()