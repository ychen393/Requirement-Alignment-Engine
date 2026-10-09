"""Pure constructors for the initial requirement-alignment flow.

All semantic content is supplied by the caller. These functions define application
boundaries for future AI suggestions without performing inference themselves.
"""

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from requirement_alignment.models import (
    AcceptanceCriterion,
    AnalysisItem,
    Deliverable,
    ExecutionPlan,
    Metric,
    RawRequirement,
    RequirementAnalysis,
    RequirementField,
    RequirementVersion,
    RiskItem,
    Task,
)


def analyze_raw_requirement(
    raw_requirement: RawRequirement,
    *,
    confirmed_information: Sequence[AnalysisItem] = (),
    missing_information: Sequence[AnalysisItem] = (),
    assumptions: Sequence[AnalysisItem] = (),
    ambiguities: Sequence[AnalysisItem] = (),
    risks: Sequence[RiskItem] = (),
    id: UUID | None = None,
    analyzed_at: datetime | None = None,
) -> RequirementAnalysis:
    values: dict[str, Any] = {
        "raw_requirement_id": raw_requirement.id,
        "confirmed_information": list(confirmed_information),
        "missing_information": list(missing_information),
        "assumptions": list(assumptions),
        "ambiguities": list(ambiguities),
        "risks": list(risks),
    }
    if id is not None:
        values["id"] = id
    if analyzed_at is not None:
        values["analyzed_at"] = analyzed_at
    return RequirementAnalysis(**values)


def create_requirement_version(
    raw_requirement: RawRequirement,
    *,
    version_number: int,
    objective: str,
    scope: Sequence[str],
    expected_outputs: Sequence[str],
    acceptance_criteria: Sequence[AcceptanceCriterion],
    created_by: str,
    out_of_scope: Sequence[str] = (),
    constraints: Sequence[str] = (),
    metrics: Sequence[Metric] = (),
    additional_fields: Sequence[RequirementField] = (),
    previous_version: RequirementVersion | None = None,
    change_summary: str | None = None,
    is_current: bool = True,
    id: UUID | None = None,
    created_at: datetime | None = None,
) -> RequirementVersion:
    if previous_version is not None and previous_version.raw_requirement_id != raw_requirement.id:
        raise ValueError("previous version must belong to the same raw requirement")
    values: dict[str, Any] = {
        "raw_requirement_id": raw_requirement.id,
        "version_number": version_number,
        "previous_version_id": previous_version.id if previous_version else None,
        "objective": objective,
        "scope": list(scope),
        "out_of_scope": list(out_of_scope),
        "constraints": list(constraints),
        "expected_outputs": list(expected_outputs),
        "metrics": list(metrics),
        "acceptance_criteria": list(acceptance_criteria),
        "additional_fields": list(additional_fields),
        "created_by": created_by,
        "change_summary": change_summary,
        "is_current": is_current,
    }
    if id is not None:
        values["id"] = id
    if created_at is not None:
        values["created_at"] = created_at
    return RequirementVersion(**values)


def create_execution_plan(
    requirement_version: RequirementVersion,
    *,
    objective: str,
    tasks: Sequence[Task],
    deliverables: Sequence[Deliverable],
    id: UUID | None = None,
    created_at: datetime | None = None,
) -> ExecutionPlan:
    values: dict[str, Any] = {
        "requirement_version_id": requirement_version.id,
        "objective": objective,
        "tasks": list(tasks),
        "deliverables": list(deliverables),
    }
    if id is not None:
        values["id"] = id
    if created_at is not None:
        values["created_at"] = created_at
    return ExecutionPlan(**values)

