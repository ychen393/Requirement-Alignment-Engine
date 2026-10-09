"""AI-assisted requirement-change analysis with selective task preservation."""

from pydantic import BaseModel, ConfigDict

from requirement_alignment.ai.planner import materialize_plan_draft
from requirement_alignment.ai.prompts import CHANGE_ANALYSIS_PROMPT
from requirement_alignment.ai.provider import AIResponseValidationError, LLMProvider
from requirement_alignment.ai.requirement_analyzer import materialize_requirement_draft
from requirement_alignment.ai.schemas import ChangeAnalysisDraft, ImpactAction, Proposal
from requirement_alignment.models import (
    ExecutionPlan,
    ImpactAnalysis,
    RawRequirement,
    RequirementDiff,
    RequirementDiffEntry,
    RequirementVersion,
    TaskImpact,
)
from requirement_alignment.services import (
    analyze_change_impact,
    create_requirement_diff,
    revise_execution_plan,
)


class ChangeProposalBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirement_version: RequirementVersion
    requirement_diff: RequirementDiff
    impact_analysis: ImpactAnalysis
    revised_execution_plan: ExecutionPlan


def analyze_requirement_change_with_ai(
    raw_requirement: RawRequirement,
    current_requirement: RequirementVersion,
    current_plan: ExecutionPlan,
    stakeholder_message: str,
    provider: LLMProvider,
) -> Proposal[ChangeProposalBundle]:
    draft = provider.generate_structured(
        CHANGE_ANALYSIS_PROMPT,
        "\n".join(
            [
                f"Current requirement: {current_requirement.model_dump_json()}",
                f"Current plan: {current_plan.model_dump_json()}",
                f"Stakeholder change: {stakeholder_message}",
            ]
        ),
        ChangeAnalysisDraft,
    )
    next_requirement = materialize_requirement_draft(
        raw_requirement,
        draft.next_requirement,
        version_number=current_requirement.version_number + 1,
        previous_version=current_requirement,
    )
    diff = create_requirement_diff(
        current_requirement,
        next_requirement,
        entries=[RequirementDiffEntry(**entry.model_dump()) for entry in draft.diff_entries],
    )

    current_by_id = {task.id: task for task in current_plan.tasks}
    decision_by_id = {item.task_id: item for item in draft.task_decisions}
    if len(decision_by_id) != len(draft.task_decisions) or set(decision_by_id) != set(current_by_id):
        raise AIResponseValidationError("AI must classify every existing task exactly once")
    plan_tasks, deliverables = materialize_plan_draft(
        next_requirement,
        draft.revised_plan,
        source_tasks=current_by_id,
    )
    revised_by_id = {task.id: task for task in plan_tasks}
    new_tasks = [task for task in plan_tasks if task.id not in current_by_id]
    keep_ids = [item.task_id for item in draft.task_decisions if item.action is ImpactAction.KEEP]
    modified_impacts = [
        TaskImpact(
            task_id=item.task_id,
            reason=item.reason,
            affected_requirement_paths=item.affected_requirement_paths,
            recommended_action=item.recommended_action,
        )
        for item in draft.task_decisions
        if item.action is ImpactAction.MODIFY
    ]
    rework_impacts = [
        TaskImpact(
            task_id=item.task_id,
            reason=item.reason,
            affected_requirement_paths=item.affected_requirement_paths,
            recommended_action=item.recommended_action,
        )
        for item in draft.task_decisions
        if item.action is ImpactAction.REWORK
    ]
    changed_ids = {item.task_id for item in [*modified_impacts, *rework_impacts]}
    if not changed_ids <= set(revised_by_id):
        raise AIResponseValidationError("modified or reworked tasks are missing from the revised plan")
    impact = analyze_change_impact(
        diff,
        valid_task_ids=keep_ids,
        tasks_needing_modification=modified_impacts,
        tasks_requiring_rework=rework_impacts,
        new_tasks_required=new_tasks,
        summary=draft.impact_summary,
    )
    revised_plan = revise_execution_plan(
        current_plan,
        next_requirement,
        diff,
        impact,
        modified_tasks=[revised_by_id[item.task_id] for item in modified_impacts],
        reworked_tasks=[revised_by_id[item.task_id] for item in rework_impacts],
        deliverables=deliverables,
        objective=draft.revised_plan.objective,
    )
    return Proposal(
        payload=ChangeProposalBundle(
            requirement_version=next_requirement,
            requirement_diff=diff,
            impact_analysis=impact,
            revised_execution_plan=revised_plan,
        )
    )
