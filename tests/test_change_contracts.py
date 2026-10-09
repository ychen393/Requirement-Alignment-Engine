from uuid import uuid4

import pytest
from pydantic import ValidationError

from requirement_alignment.models import (
    DiffCategory,
    ImpactAnalysis,
    RequirementDiffEntry,
    TaskImpact,
)
from tests.fixtures.model_benchmarking import DIFF, IMPACT_ANALYSIS, PREPARE_TASK_ID


def test_diff_contains_every_required_category() -> None:
    assert {entry.category for entry in DIFF.entries} == set(DiffCategory)
    assert len(DIFF.added) == 3
    assert len(DIFF.removed) == 1
    assert len(DIFF.modified) == 1
    assert len(DIFF.unchanged) == 1


def test_modified_diff_requires_different_values() -> None:
    with pytest.raises(ValidationError, match="different values"):
        RequirementDiffEntry(
            field_path="objective",
            category=DiffCategory.MODIFIED,
            old_value="same",
            new_value="same",
            explanation="invalid",
        )


def test_impact_analysis_keeps_adjusts_and_adds_work_selectively() -> None:
    assert IMPACT_ANALYSIS.valid_task_ids
    assert IMPACT_ANALYSIS.tasks_needing_modification
    assert IMPACT_ANALYSIS.new_tasks_required
    assert IMPACT_ANALYSIS.tasks_requiring_rework == []


def test_impact_categories_cannot_overlap() -> None:
    with pytest.raises(ValidationError, match="must not overlap"):
        ImpactAnalysis(
            requirement_diff_id=uuid4(),
            valid_task_ids=[PREPARE_TASK_ID],
            tasks_needing_modification=[
                TaskImpact(
                    task_id=PREPARE_TASK_ID,
                    reason="conflict",
                    recommended_action="fix",
                )
            ],
            summary="invalid overlap",
        )
