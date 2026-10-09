from uuid import uuid4

import pytest

from requirement_alignment.services import (
    analyze_change_impact,
    analyze_raw_requirement,
    apply_requirement_change,
    create_execution_plan,
    create_requirement_diff,
    create_requirement_version,
    evaluate_completion,
    revise_execution_plan,
)
from tests.fixtures.model_benchmarking import (
    ANALYSIS,
    COMPLETION_EVALUATION,
    DIFF,
    EXECUTION_PLAN,
    IMPACT_ANALYSIS,
    RAW_REQUIREMENT,
    VERSION_V1,
    VERSION_V2,
)


def test_thin_services_construct_connected_domain_objects() -> None:
    analysis = analyze_raw_requirement(
        RAW_REQUIREMENT,
        confirmed_information=ANALYSIS.confirmed_information,
        missing_information=ANALYSIS.missing_information,
    )
    assert analysis.raw_requirement_id == RAW_REQUIREMENT.id

    version = create_requirement_version(
        RAW_REQUIREMENT,
        version_number=1,
        objective=VERSION_V1.objective,
        scope=VERSION_V1.scope,
        out_of_scope=VERSION_V1.out_of_scope,
        constraints=VERSION_V1.constraints,
        expected_outputs=VERSION_V1.expected_outputs,
        metrics=VERSION_V1.metrics,
        acceptance_criteria=VERSION_V1.acceptance_criteria,
        additional_fields=VERSION_V1.additional_fields,
        created_by="test",
    )
    plan = create_execution_plan(
        version,
        objective=EXECUTION_PLAN.objective,
        tasks=EXECUTION_PLAN.tasks,
        deliverables=EXECUTION_PLAN.deliverables,
    )
    assert plan.requirement_version_id == version.id

    change = apply_requirement_change(
        VERSION_V1,
        VERSION_V2,
        requested_by="stakeholder",
        reason="scope changed",
        requested_changes=["add project validation"],
    )
    diff = create_requirement_diff(VERSION_V1, VERSION_V2, entries=DIFF.entries)
    impact = analyze_change_impact(
        diff,
        valid_task_ids=IMPACT_ANALYSIS.valid_task_ids,
        tasks_needing_modification=IMPACT_ANALYSIS.tasks_needing_modification,
        new_tasks_required=IMPACT_ANALYSIS.new_tasks_required,
        summary=IMPACT_ANALYSIS.summary,
    )
    assert change.resulting_version_id == VERSION_V2.id
    assert impact.requirement_diff_id == diff.id


def test_evaluation_service_rejects_a_stale_plan() -> None:
    with pytest.raises(ValueError, match="current requirement plan"):
        evaluate_completion(
            VERSION_V2,
            EXECUTION_PLAN,
            criterion_results=COMPLETION_EVALUATION.criterion_results,
            overall_status=COMPLETION_EVALUATION.overall_status,
            unresolved_items=COMPLETION_EVALUATION.unresolved_items,
        )


def test_revised_plan_requires_every_impacted_modified_task() -> None:
    with pytest.raises(ValueError, match="exactly match"):
        revise_execution_plan(
            EXECUTION_PLAN,
            VERSION_V2,
            DIFF,
            IMPACT_ANALYSIS,
            modified_tasks=[],
            deliverables=EXECUTION_PLAN.deliverables,
            id=uuid4(),
        )
