"""Pure application functions for requirement changes and revised planning."""

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from requirement_alignment.models import (
    Deliverable,
    ExecutionPlan,
    ImpactAnalysis,
    RequirementChange,
    RequirementDiff,
    RequirementDiffEntry,
    RequirementVersion,
    Task,
    TaskImpact,
)
from requirement_alignment.services.requirement_flow import create_execution_plan


def apply_requirement_change(
    previous_version: RequirementVersion,
    resulting_version: RequirementVersion,
    *,
    requested_by: str,
    reason: str,
    requested_changes: Sequence[str],
    id: UUID | None = None,
    requested_at: datetime | None = None,
) -> RequirementChange:
    if resulting_version.raw_requirement_id != previous_version.raw_requirement_id:
        raise ValueError("changed versions must belong to the same raw requirement")
    if resulting_version.previous_version_id != previous_version.id:
        raise ValueError("resulting version must reference the previous version")
    values: dict[str, Any] = {
        "from_version_id": previous_version.id,
        "resulting_version_id": resulting_version.id,
        "requested_by": requested_by,
        "reason": reason,
        "requested_changes": list(requested_changes),
    }
    if id is not None:
        values["id"] = id
    if requested_at is not None:
        values["requested_at"] = requested_at
    return RequirementChange(**values)


def create_requirement_diff(
    previous_version: RequirementVersion,
    resulting_version: RequirementVersion,
    *,
    entries: Sequence[RequirementDiffEntry],
    id: UUID | None = None,
) -> RequirementDiff:
    if resulting_version.previous_version_id != previous_version.id:
        raise ValueError("diff versions must be directly related")
    values: dict[str, Any] = {
        "from_version_id": previous_version.id,
        "to_version_id": resulting_version.id,
        "entries": list(entries),
    }
    if id is not None:
        values["id"] = id
    return RequirementDiff(**values)


def analyze_change_impact(
    requirement_diff: RequirementDiff,
    *,
    valid_task_ids: Sequence[UUID] = (),
    tasks_needing_modification: Sequence[TaskImpact] = (),
    tasks_requiring_rework: Sequence[TaskImpact] = (),
    new_tasks_required: Sequence[Task] = (),
    affected_deliverable_ids: Sequence[UUID] = (),
    affected_criterion_ids: Sequence[UUID] = (),
    summary: str,
    id: UUID | None = None,
    analyzed_at: datetime | None = None,
) -> ImpactAnalysis:
    values: dict[str, Any] = {
        "requirement_diff_id": requirement_diff.id,
        "valid_task_ids": list(valid_task_ids),
        "tasks_needing_modification": list(tasks_needing_modification),
        "tasks_requiring_rework": list(tasks_requiring_rework),
        "new_tasks_required": list(new_tasks_required),
        "affected_deliverable_ids": list(affected_deliverable_ids),
        "affected_criterion_ids": list(affected_criterion_ids),
        "summary": summary,
    }
    if id is not None:
        values["id"] = id
    if analyzed_at is not None:
        values["analyzed_at"] = analyzed_at
    return ImpactAnalysis(**values)


def revise_execution_plan(
    previous_plan: ExecutionPlan,
    new_requirement_version: RequirementVersion,
    requirement_diff: RequirementDiff,
    impact_analysis: ImpactAnalysis,
    *,
    modified_tasks: Sequence[Task],
    reworked_tasks: Sequence[Task] = (),
    deliverables: Sequence[Deliverable],
    objective: str | None = None,
    id: UUID | None = None,
    created_at: datetime | None = None,
) -> ExecutionPlan:
    if requirement_diff.from_version_id != previous_plan.requirement_version_id:
        raise ValueError("diff source must match the previous execution plan")
    if requirement_diff.to_version_id != new_requirement_version.id:
        raise ValueError("diff target must match the new requirement version")
    if impact_analysis.requirement_diff_id != requirement_diff.id:
        raise ValueError("impact analysis must belong to the supplied diff")
    previous_by_id = {task.id: task for task in previous_plan.tasks}
    previous_ids = set(previous_by_id)
    valid_ids = set(impact_analysis.valid_task_ids)
    modified_ids = {item.task_id for item in impact_analysis.tasks_needing_modification}
    reworked_ids = {item.task_id for item in impact_analysis.tasks_requiring_rework}
    supplied_modified_ids = {task.id for task in modified_tasks}
    supplied_reworked_ids = {task.id for task in reworked_tasks}

    if not (valid_ids | modified_ids | reworked_ids) <= previous_ids:
        raise ValueError("impact analysis references tasks outside the previous plan")
    if supplied_modified_ids != modified_ids:
        raise ValueError("modified tasks must exactly match the impact analysis")
    if supplied_reworked_ids != reworked_ids:
        raise ValueError("reworked tasks must exactly match the impact analysis")
    new_ids = {task.id for task in impact_analysis.new_tasks_required}
    if new_ids & previous_ids:
        raise ValueError("new tasks must use IDs not present in the previous plan")

    preserved_tasks = [previous_by_id[task.id] for task in previous_plan.tasks if task.id in valid_ids]
    revised_tasks = [
        *preserved_tasks,
        *modified_tasks,
        *reworked_tasks,
        *impact_analysis.new_tasks_required,
    ]
    revised_tasks.sort(key=lambda task: task.execution_order)
    return create_execution_plan(
        new_requirement_version,
        objective=objective or previous_plan.objective,
        tasks=revised_tasks,
        deliverables=deliverables,
        id=id,
        created_at=created_at,
    )
