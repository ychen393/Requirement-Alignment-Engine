"""Evidence-bound AI completion evaluation."""

from requirement_alignment.ai.prompts import COMPLETION_EVALUATION_PROMPT
from requirement_alignment.ai.provider import AIResponseValidationError, LLMProvider
from requirement_alignment.ai.schemas import (
    CompletionEvaluationDraft,
    EvidenceItem,
    Proposal,
)
from requirement_alignment.models import (
    CompletionEvaluation,
    CriterionEvaluation,
    CriterionStatus,
    ExecutionPlan,
    RequirementVersion,
)
from requirement_alignment.services import evaluate_completion


def evaluate_completion_with_ai(
    current_requirement: RequirementVersion,
    current_plan: ExecutionPlan,
    evidence_status: list[EvidenceItem],
    provider: LLMProvider,
) -> Proposal[CompletionEvaluation]:
    draft = provider.generate_structured(
        COMPLETION_EVALUATION_PROMPT,
        "\n".join(
            [
                f"Current requirement: {current_requirement.model_dump_json()}",
                f"Current plan: {current_plan.model_dump_json()}",
                "User-provided evidence/status:",
                *[item.model_dump_json() for item in evidence_status],
            ]
        ),
        CompletionEvaluationDraft,
    )
    evidence_by_criterion = {item.criterion_id: set(item.evidence) for item in evidence_status}
    results: list[CriterionEvaluation] = []
    for item in draft.criterion_results:
        supplied = evidence_by_criterion.get(item.criterion_id, set())
        if not set(item.evidence) <= supplied:
            raise AIResponseValidationError("AI completion result contains evidence not supplied by the user")
        values = item.model_dump()
        if not supplied:
            values.update(
                status=CriterionStatus.MISSING_EVIDENCE,
                evidence=[],
                explanation="No user-provided evidence is available for this criterion",
            )
        results.append(CriterionEvaluation(**values))
    overall = draft.overall_status
    if any(result.status is not CriterionStatus.PASS for result in results) and overall.value == "COMPLETED":
        from requirement_alignment.models import CompletionStatus

        overall = CompletionStatus.BLOCKED_BY_MISSING_EVIDENCE
    evaluation = evaluate_completion(
        current_requirement,
        current_plan,
        criterion_results=results,
        overall_status=overall,
        unresolved_items=draft.unresolved_items or ["Review missing completion evidence"],
    )
    return Proposal(payload=evaluation)

