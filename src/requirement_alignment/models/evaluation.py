"""Completion-evaluation contracts."""

from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from requirement_alignment.models.common import (
    CompletionStatus,
    CriterionStatus,
    IdentifiedModel,
    UTCDateTime,
    utc_now,
)


class CriterionEvaluation(IdentifiedModel):
    criterion_id: UUID
    status: CriterionStatus
    evidence: list[str] = Field(default_factory=list)
    observed_value: Any = None
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_evidence_status(self) -> "CriterionEvaluation":
        if self.status is CriterionStatus.PASS and not self.evidence:
            raise ValueError("passing a criterion requires evidence")
        if self.status is CriterionStatus.MISSING_EVIDENCE and self.evidence:
            raise ValueError("missing-evidence criteria cannot contain evidence")
        return self


class CompletionEvaluation(IdentifiedModel):
    requirement_version_id: UUID
    execution_plan_id: UUID
    criterion_results: list[CriterionEvaluation] = Field(min_length=1)
    completed_criteria: list[UUID] = Field(default_factory=list)
    failed_criteria: list[UUID] = Field(default_factory=list)
    missing_evidence: list[UUID] = Field(default_factory=list)
    overall_status: CompletionStatus
    unresolved_items: list[str] = Field(default_factory=list)
    evaluated_at: UTCDateTime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_summary_consistency(self) -> "CompletionEvaluation":
        result_ids = [result.criterion_id for result in self.criterion_results]
        if len(result_ids) != len(set(result_ids)):
            raise ValueError("each acceptance criterion may be evaluated only once")
        expected_completed = {
            result.criterion_id
            for result in self.criterion_results
            if result.status is CriterionStatus.PASS
        }
        expected_failed = {
            result.criterion_id
            for result in self.criterion_results
            if result.status is CriterionStatus.FAIL
        }
        expected_missing = {
            result.criterion_id
            for result in self.criterion_results
            if result.status is CriterionStatus.MISSING_EVIDENCE
        }
        if set(self.completed_criteria) != expected_completed:
            raise ValueError("completed_criteria must match PASS results")
        if set(self.failed_criteria) != expected_failed:
            raise ValueError("failed_criteria must match FAIL results")
        if set(self.missing_evidence) != expected_missing:
            raise ValueError("missing_evidence must match MISSING_EVIDENCE results")
        all_pass = all(
            result.status is CriterionStatus.PASS for result in self.criterion_results
        )
        if (self.overall_status is CompletionStatus.COMPLETED) != all_pass:
            raise ValueError("COMPLETED is valid if and only if every criterion passes")
        if not all_pass and not self.unresolved_items:
            raise ValueError("incomplete evaluations require unresolved items")
        return self
