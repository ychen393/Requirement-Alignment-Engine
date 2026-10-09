"""Domain-specific exceptions."""


class InvalidStateTransition(ValueError):
    """Raised when a workflow state transition is not allowed."""

