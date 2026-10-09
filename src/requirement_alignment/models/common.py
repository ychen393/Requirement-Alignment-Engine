"""Shared types and enums."""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def require_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must use UTC")
    return value


UTCDateTime = Annotated[datetime, AfterValidator(require_utc)]


class DomainModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, validate_default=True
    )


class IdentifiedModel(DomainModel):
    id: UUID = Field(default_factory=uuid4)


class TimestampedModel(IdentifiedModel):
    created_at: UTCDateTime = Field(default_factory=utc_now)


class WorkflowState(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    ALIGNED = "ALIGNED"
    IN_EXECUTION = "IN_EXECUTION"
    CHANGED = "CHANGED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    COMPLETED = "COMPLETED"


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FieldType(str, Enum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    ENUM = "ENUM"
    LIST = "LIST"
    OBJECT = "OBJECT"


class QuestionStatus(str, Enum):
    OPEN = "OPEN"
    ANSWERED = "ANSWERED"
    DISMISSED = "DISMISSED"


class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    INVALIDATED = "INVALIDATED"


class DeliverableStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    READY = "READY"
    ACCEPTED = "ACCEPTED"


class MetricOperator(str, Enum):
    EQ = "EQ"
    GTE = "GTE"
    LTE = "LTE"
    GT = "GT"
    LT = "LT"
    BETWEEN = "BETWEEN"


class DiffCategory(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"


class CriterionStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    NOT_YET_COMPLETE = "NOT_YET_COMPLETE"


class CompletionStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED"
    FAILED = "FAILED"
    BLOCKED_BY_MISSING_EVIDENCE = "BLOCKED_BY_MISSING_EVIDENCE"


__all__ = [
    "CompletionStatus",
    "CriterionStatus",
    "DeliverableStatus",
    "DiffCategory",
    "DomainModel",
    "FieldType",
    "IdentifiedModel",
    "MetricOperator",
    "Priority",
    "QuestionStatus",
    "TaskStatus",
    "TimestampedModel",
    "UTCDateTime",
    "WorkflowState",
    "utc_now",
]
