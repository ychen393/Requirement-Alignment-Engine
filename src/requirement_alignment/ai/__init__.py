"""AI proposal layer. It never directly confirms or mutates domain state."""

from requirement_alignment.ai.change_analyzer import analyze_requirement_change_with_ai
from requirement_alignment.ai.completion_evaluator import evaluate_completion_with_ai
from requirement_alignment.ai.planner import generate_execution_plan_with_ai
from requirement_alignment.ai.provider import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    AIResponseValidationError,
    AITimeoutError,
    LLMProvider,
    OpenAICompatibleProvider,
)
from requirement_alignment.ai.requirement_analyzer import (
    analyze_requirement_with_ai,
    generate_clarification_questions_with_ai,
    generate_requirement_proposal_with_ai,
)
from requirement_alignment.ai.schemas import ConfirmationStatus, Proposal, confirm_proposal

__all__ = [
    "AIConfigurationError",
    "AIProviderError",
    "AIResponseError",
    "AIResponseValidationError",
    "AITimeoutError",
    "ConfirmationStatus",
    "LLMProvider",
    "OpenAICompatibleProvider",
    "Proposal",
    "analyze_requirement_change_with_ai",
    "analyze_requirement_with_ai",
    "confirm_proposal",
    "evaluate_completion_with_ai",
    "generate_clarification_questions_with_ai",
    "generate_execution_plan_with_ai",
    "generate_requirement_proposal_with_ai",
]

