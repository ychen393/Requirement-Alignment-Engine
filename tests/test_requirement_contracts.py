from datetime import datetime

import pytest
from pydantic import ValidationError

from requirement_alignment.models import Metric, MetricOperator, RequirementVersion
from tests.fixtures.model_benchmarking import (
    ANALYSIS,
    CLARIFICATION_QUESTIONS,
    RAW_REQUIREMENT,
    VERSION_V1,
    VERSION_V2,
)


def test_complete_requirement_flow_has_expected_versions() -> None:
    assert ANALYSIS.raw_requirement_id == RAW_REQUIREMENT.id
    assert len(CLARIFICATION_QUESTIONS) == 9
    assert all(question.answer for question in CLARIFICATION_QUESTIONS)
    assert VERSION_V1.label == "V1"
    assert VERSION_V2.label == "V2"
    assert VERSION_V2.previous_version_id == VERSION_V1.id
    assert VERSION_V2.objective == VERSION_V1.objective


def test_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RequirementVersion.model_validate(
            {**VERSION_V1.model_dump(), "unexpected": True}
        )


def test_raw_requirement_rejects_naive_timestamp() -> None:
    data = RAW_REQUIREMENT.model_dump()
    data["created_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError, match="timezone-aware"):
        type(RAW_REQUIREMENT).model_validate(data)


def test_between_metric_requires_two_ordered_bounds() -> None:
    with pytest.raises(ValidationError, match="exactly two"):
        Metric(
            name="acceptable range",
            description="range",
            measurement_method="measure",
            target_operator=MetricOperator.BETWEEN,
            target_value=[1],
        )
