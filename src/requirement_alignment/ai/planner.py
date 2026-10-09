"""AI-assisted execution planning with deterministic reference resolution."""

from collections.abc import Mapping
from uuid import UUID, uuid4

from requirement_alignment.ai.prompts import EXECUTION_PLAN_PROMPT
from requirement_alignment.ai.provider import AIResponseValidationError, LLMProvider
from requirement_alignment.ai.schemas import ExecutionPlanDraft, Proposal
from requirement_alignment.models import Deliverable, ExecutionPlan, RequirementVersion, Task
from requirement_alignment.services import create_execution_plan


def materialize_plan_draft(
    requirement: RequirementVersion,
    draft: ExecutionPlanDraft,
    *,
    source_tasks: Mapping[UUID, Task] | None = None,
) -> tuple[list[Task], list[Deliverable]]:
    source_tasks = source_tasks or {}
    if len({item.key for item in draft.tasks}) != len(draft.tasks):
        raise AIResponseValidationError("AI proposed duplicate task keys")
    if len({item.key for item in draft.deliverables}) != len(draft.deliverables):
        raise AIResponseValidationError("AI proposed duplicate deliverable keys")

    criterion_ids = {item.title: item.id for item in requirement.acceptance_criteria}
    if len(criterion_ids) != len(requirement.acceptance_criteria):
        raise AIResponseValidationError("acceptance criterion titles must be unique for AI planning")
    task_ids: dict[str, UUID] = {}
    for item in draft.tasks:
        if item.source_task_id is not None and item.source_task_id not in source_tasks:
            raise AIResponseValidationError("revised task references an unknown source task")
        task_ids[item.key] = item.source_task_id or uuid4()
    if len(set(task_ids.values())) != len(task_ids):
        raise AIResponseValidationError("AI proposed duplicate task identities")
    deliverable_ids = {item.key: uuid4() for item in draft.deliverables}

    tasks: list[Task] = []
    for item in draft.tasks:
        try:
            dependencies = [task_ids[key] for key in item.dependency_keys]
            deliverables = [deliverable_ids[key] for key in item.deliverable_keys]
            criteria = [criterion_ids[title] for title in item.acceptance_criterion_titles]
        except KeyError as exc:
            raise AIResponseValidationError(f"AI plan contains an unknown reference: {exc.args[0]}") from exc
        source = source_tasks.get(item.source_task_id) if item.source_task_id else None
        tasks.append(
            Task(
                id=task_ids[item.key],
                title=item.title,
                description=item.description,
                status=source.status if source else "NOT_STARTED",
                dependencies=dependencies,
                requirement_references=item.requirement_references,
                acceptance_criterion_ids=criteria,
                deliverable_ids=deliverables,
                estimated_effort_hours=item.estimated_effort_hours,
                execution_order=item.execution_order,
            )
        )
    deliverable_models: list[Deliverable] = []
    for item in draft.deliverables:
        try:
            linked_tasks = [task_ids[key] for key in item.task_keys]
            criteria = [criterion_ids[title] for title in item.acceptance_criterion_titles]
        except KeyError as exc:
            raise AIResponseValidationError(f"AI deliverable contains an unknown reference: {exc.args[0]}") from exc
        deliverable_models.append(
            Deliverable(
                id=deliverable_ids[item.key],
                name=item.name,
                description=item.description,
                format=item.format,
                task_ids=linked_tasks,
                acceptance_criterion_ids=criteria,
            )
        )
    return tasks, deliverable_models


def generate_execution_plan_with_ai(
    confirmed_requirement: RequirementVersion,
    provider: LLMProvider,
) -> Proposal[ExecutionPlan]:
    draft = provider.generate_structured(
        EXECUTION_PLAN_PROMPT,
        confirmed_requirement.model_dump_json(),
        ExecutionPlanDraft,
    )
    tasks, deliverables = materialize_plan_draft(confirmed_requirement, draft)
    plan = create_execution_plan(
        confirmed_requirement,
        objective=draft.objective,
        tasks=tasks,
        deliverables=deliverables,
    )
    return Proposal(payload=plan)

