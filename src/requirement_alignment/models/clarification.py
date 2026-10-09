"""Clarification question contract."""

from uuid import UUID

from pydantic import Field, model_validator

from requirement_alignment.models.common import (
    IdentifiedModel,
    Priority,
    QuestionStatus,
    UTCDateTime,
)


class ClarificationQuestion(IdentifiedModel):
    analysis_id: UUID
    question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    target_field: str = Field(min_length=1)
    priority: Priority = Priority.MEDIUM
    status: QuestionStatus = QuestionStatus.OPEN
    answer: str | None = None
    answered_by: str | None = None
    answered_at: UTCDateTime | None = None

    @model_validator(mode="after")
    def validate_answer_state(self) -> "ClarificationQuestion":
        answer_fields = (self.answer, self.answered_by, self.answered_at)
        if self.status is QuestionStatus.ANSWERED:
            if any(value is None for value in answer_fields):
                raise ValueError("answered questions require answer, author, and timestamp")
        elif any(value is not None for value in answer_fields):
            raise ValueError("only answered questions may contain answer details")
        return self
