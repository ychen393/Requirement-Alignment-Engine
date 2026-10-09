import pytest
from pydantic import ValidationError

from requirement_alignment.models import CompletionEvaluation, CompletionStatus
from tests.fixtures.model_benchmarking import COMPLETION_EVALUATION


def test_fixture_is_not_complete_when_requirements_are_unresolved() -> None:
    assert COMPLETION_EVALUATION.overall_status is CompletionStatus.PARTIALLY_COMPLETED
    assert len(COMPLETION_EVALUATION.completed_criteria) == 2
    assert len(COMPLETION_EVALUATION.missing_evidence) == 3
    assert COMPLETION_EVALUATION.unresolved_items


def test_completed_status_requires_every_criterion_to_pass() -> None:
    data = COMPLETION_EVALUATION.model_dump()
    data["overall_status"] = CompletionStatus.COMPLETED
    with pytest.raises(ValidationError, match="if and only if every criterion passes"):
        CompletionEvaluation.model_validate(data)


def test_summary_lists_must_match_result_statuses() -> None:
    data = COMPLETION_EVALUATION.model_dump()
    data["completed_criteria"] = []
    with pytest.raises(ValidationError, match="must match PASS results"):
        CompletionEvaluation.model_validate(data)
