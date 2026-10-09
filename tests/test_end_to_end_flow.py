"""Verification of the complete deterministic Phase 2 business flow."""

from requirement_alignment.models import CriterionStatus, DiffCategory, QuestionStatus
from tests.fixtures.model_benchmarking import (
    ANALYSIS,
    CHANGE,
    CLARIFICATION_QUESTIONS,
    COMPLETION_EVALUATION,
    DIFF,
    EXECUTION_PLAN,
    EXECUTION_PLAN_V2,
    IMPACT_ANALYSIS,
    RAW_REQUIREMENT,
    VERSION_V1,
    VERSION_V2,
)


def test_complete_workflow_chain_and_references_are_consistent() -> None:
    # Raw request -> analysis -> answered clarification -> V1
    assert ANALYSIS.raw_requirement_id == RAW_REQUIREMENT.id
    assert {question.analysis_id for question in CLARIFICATION_QUESTIONS} == {ANALYSIS.id}
    assert all(question.status is QuestionStatus.ANSWERED for question in CLARIFICATION_QUESTIONS)
    assert VERSION_V1.raw_requirement_id == RAW_REQUIREMENT.id

    # V1 -> plan -> change -> V2 -> diff -> impact -> completion
    assert EXECUTION_PLAN.requirement_version_id == VERSION_V1.id
    assert CHANGE.from_version_id == VERSION_V1.id
    assert CHANGE.resulting_version_id == VERSION_V2.id
    assert VERSION_V2.previous_version_id == VERSION_V1.id
    assert VERSION_V2.raw_requirement_id == RAW_REQUIREMENT.id
    assert (DIFF.from_version_id, DIFF.to_version_id) == (VERSION_V1.id, VERSION_V2.id)
    assert IMPACT_ANALYSIS.requirement_diff_id == DIFF.id
    assert COMPLETION_EVALUATION.requirement_version_id == VERSION_V2.id
    assert EXECUTION_PLAN_V2.requirement_version_id == VERSION_V2.id
    assert COMPLETION_EVALUATION.execution_plan_id == EXECUTION_PLAN_V2.id

    # Every plan reference points to an object in its owning V1 contract.
    task_ids = {task.id for task in EXECUTION_PLAN.tasks}
    deliverable_ids = {item.id for item in EXECUTION_PLAN.deliverables}
    v1_criterion_ids = {item.id for item in VERSION_V1.acceptance_criteria}
    assert len(EXECUTION_PLAN.tasks) == 7
    for task in EXECUTION_PLAN.tasks:
        assert set(task.dependencies) <= task_ids
        assert set(task.deliverable_ids) <= deliverable_ids
        assert set(task.acceptance_criterion_ids) <= v1_criterion_ids
    for deliverable in EXECUTION_PLAN.deliverables:
        assert set(deliverable.task_ids) <= task_ids
        assert set(deliverable.acceptance_criterion_ids) <= v1_criterion_ids

    # Impact references distinguish retained, adjusted, and new work.
    impacted_existing_ids = (
        set(IMPACT_ANALYSIS.valid_task_ids)
        | {item.task_id for item in IMPACT_ANALYSIS.tasks_needing_modification}
        | {item.task_id for item in IMPACT_ANALYSIS.tasks_requiring_rework}
    )
    assert impacted_existing_ids <= task_ids
    assert IMPACT_ANALYSIS.tasks_requiring_rework == []
    assert len(IMPACT_ANALYSIS.new_tasks_required) == 5

    v1_by_id = {task.id: task for task in EXECUTION_PLAN.tasks}
    v2_by_id = {task.id: task for task in EXECUTION_PLAN_V2.tasks}
    assert set(IMPACT_ANALYSIS.valid_task_ids) <= set(v2_by_id)
    assert all(v2_by_id[task_id] == v1_by_id[task_id] for task_id in IMPACT_ANALYSIS.valid_task_ids)
    modified_ids = {item.task_id for item in IMPACT_ANALYSIS.tasks_needing_modification}
    assert modified_ids <= set(v2_by_id)
    assert all(v2_by_id[task_id] != v1_by_id[task_id] for task_id in modified_ids)
    new_ids = {task.id for task in IMPACT_ANALYSIS.new_tasks_required}
    assert new_ids.isdisjoint(v1_by_id)
    assert new_ids <= set(v2_by_id)
    assert len(v2_by_id) == len(EXECUTION_PLAN_V2.tasks)
    assert {task.title for task in IMPACT_ANALYSIS.new_tasks_required} <= {
        task.title for task in EXECUTION_PLAN_V2.tasks
    }
    assert "Configure candidate models" not in {task.title for task in EXECUTION_PLAN_V2.tasks}

    v2_criterion_ids = {item.id for item in VERSION_V2.acceptance_criteria}
    v2_deliverable_ids = {item.id for item in EXECUTION_PLAN_V2.deliverables}
    for task in EXECUTION_PLAN_V2.tasks:
        assert set(task.dependencies) <= set(v2_by_id)
        assert set(task.deliverable_ids) <= v2_deliverable_ids
        assert set(task.acceptance_criterion_ids) <= v2_criterion_ids
    for deliverable in EXECUTION_PLAN_V2.deliverables:
        assert set(deliverable.task_ids) <= set(v2_by_id)
        assert set(deliverable.acceptance_criterion_ids) <= v2_criterion_ids

    # V2 evaluation covers every criterion once and intentionally remains incomplete.
    evaluated_ids = {item.criterion_id for item in COMPLETION_EVALUATION.criterion_results}
    assert evaluated_ids == v2_criterion_ids
    assert {entry.category for entry in DIFF.entries} == set(DiffCategory)
    assert any(
        result.status is not CriterionStatus.PASS
        for result in COMPLETION_EVALUATION.criterion_results
    )
    assert COMPLETION_EVALUATION.overall_status.value != "COMPLETED"
