import pytest

from requirement_alignment.exceptions import InvalidStateTransition
from requirement_alignment.models import WorkflowState
from requirement_alignment.state_machine import can_transition, validate_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkflowState.DRAFT, WorkflowState.NEEDS_CLARIFICATION),
        (WorkflowState.DRAFT, WorkflowState.ALIGNED),
        (WorkflowState.NEEDS_CLARIFICATION, WorkflowState.ALIGNED),
        (WorkflowState.ALIGNED, WorkflowState.IN_EXECUTION),
        (WorkflowState.IN_EXECUTION, WorkflowState.CHANGED),
        (WorkflowState.CHANGED, WorkflowState.IN_EXECUTION),
        (WorkflowState.IN_EXECUTION, WorkflowState.READY_FOR_REVIEW),
        (WorkflowState.READY_FOR_REVIEW, WorkflowState.COMPLETED),
    ],
)
def test_allowed_transitions(current: WorkflowState, target: WorkflowState) -> None:
    assert can_transition(current, target)
    validate_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (WorkflowState.DRAFT, WorkflowState.COMPLETED),
        (WorkflowState.NEEDS_CLARIFICATION, WorkflowState.IN_EXECUTION),
        (WorkflowState.COMPLETED, WorkflowState.CHANGED),
        (WorkflowState.IN_EXECUTION, WorkflowState.DRAFT),
    ],
)
def test_invalid_transitions(current: WorkflowState, target: WorkflowState) -> None:
    assert not can_transition(current, target)
    with pytest.raises(InvalidStateTransition):
        validate_transition(current, target)

