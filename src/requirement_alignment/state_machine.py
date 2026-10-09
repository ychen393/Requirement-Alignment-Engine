"""Pure workflow-state transition rules."""

from requirement_alignment.exceptions import InvalidStateTransition
from requirement_alignment.models.common import WorkflowState

ALLOWED_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.DRAFT: frozenset(
        {WorkflowState.NEEDS_CLARIFICATION, WorkflowState.ALIGNED}
    ),
    WorkflowState.NEEDS_CLARIFICATION: frozenset({WorkflowState.ALIGNED}),
    WorkflowState.ALIGNED: frozenset(
        {WorkflowState.IN_EXECUTION, WorkflowState.CHANGED}
    ),
    WorkflowState.IN_EXECUTION: frozenset(
        {WorkflowState.CHANGED, WorkflowState.READY_FOR_REVIEW}
    ),
    WorkflowState.CHANGED: frozenset(
        {
            WorkflowState.NEEDS_CLARIFICATION,
            WorkflowState.ALIGNED,
            WorkflowState.IN_EXECUTION,
        }
    ),
    WorkflowState.READY_FOR_REVIEW: frozenset(
        {WorkflowState.CHANGED, WorkflowState.COMPLETED}
    ),
    WorkflowState.COMPLETED: frozenset(),
}


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def validate_transition(current: WorkflowState, target: WorkflowState) -> None:
    if not can_transition(current, target):
        raise InvalidStateTransition(
            f"Transition from {current.value} to {target.value} is not allowed"
        )

