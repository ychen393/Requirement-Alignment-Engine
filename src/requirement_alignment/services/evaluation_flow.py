"""Completion-evaluation application boundary."""

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from requirement_alignment.models import (
    CompletionEvaluation,
    CompletionStatus,
    CriterionEvaluation,
    CriterionStatus,
    ExecutionPlan,
    RequirementVersion,
)


def evaluate_completion(
    requirement_version: RequirementVersion,
    execution_plan: ExecutionPlan,
    *,
    criterion_results: Sequence[CriterionEvaluation],
    overall_status: CompletionStatus,
    unresolved_items: Sequence[str] = (),
    id: UUID | None = None,
    evaluated_at: datetime | None = None,
) -> CompletionEvaluation:
    if execution_plan.requirement_version_id != requirement_version.id:
        raise ValueError("completion evaluation requires the current requirement plan")
    requirement_criteria = {criterion.id for criterion in requirement_version.acceptance_criteria}
    result_criteria = {result.criterion_id for result in criterion_results}
    if result_criteria != requirement_criteria:
        raise ValueError("criterion results must cover the current requirement exactly once")

    results = list(criterion_results)
    values: dict[str, Any] = {
        "requirement_version_id": requirement_version.id,
        "execution_plan_id": execution_plan.id,
        "criterion_results": results,
        "completed_criteria": [item.criterion_id for item in results if item.status is CriterionStatus.PASS],
        "failed_criteria": [item.criterion_id for item in results if item.status is CriterionStatus.FAIL],
        "missing_evidence": [item.criterion_id for item in results if item.status is CriterionStatus.MISSING_EVIDENCE],
        "overall_status": overall_status,
        "unresolved_items": list(unresolved_items),
    }
    if id is not None:
        values["id"] = id
    if evaluated_at is not None:
        values["evaluated_at"] = evaluated_at
    return CompletionEvaluation(**values)

