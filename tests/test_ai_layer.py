from typing import Any

from requirement_alignment.ai import (
    ConfirmationStatus,
    analyze_requirement_with_ai,
    confirm_proposal,
    evaluate_completion_with_ai,
    generate_clarification_questions_with_ai,
)
from requirement_alignment.ai.schemas import (
    AnalysisItemDraft,
    ClarificationQuestionDraft,
    ClarificationQuestionsDraft,
    CompletionEvaluationDraft,
    CriterionEvaluationDraft,
    RequirementAnalysisDraft,
)
from requirement_alignment.models import CompletionStatus, CriterionStatus
from tests.fixtures.model_benchmarking import (
    ANALYSIS,
    EXECUTION_PLAN_V2,
    RAW_REQUIREMENT,
    VERSION_V2,
)


class QueueProvider:
    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.requested_models: list[type] = []

    def generate_structured(self, system_prompt, user_prompt, response_model):
        self.requested_models.append(response_model)
        response = self.responses.pop(0)
        return response_model.model_validate(response)


def test_ai_analysis_and_questions_are_suggestions() -> None:
    provider = QueueProvider(
        RequirementAnalysisDraft(
            confirmed_information=[AnalysisItemDraft(description="Multiple models")],
            missing_information=[AnalysisItemDraft(description="Dataset missing")],
            assumptions=[],
            ambiguities=[],
            risks=[],
        ),
        ClarificationQuestionsDraft(
            questions=[
                ClarificationQuestionDraft(
                    question="Which dataset?",
                    rationale="It changes benchmark validity",
                    target_field="dataset",
                )
            ]
        ),
    )
    analysis = analyze_requirement_with_ai(RAW_REQUIREMENT, provider)
    questions = generate_clarification_questions_with_ai(
        RAW_REQUIREMENT, analysis.payload, provider
    )
    assert analysis.confirmation_status is ConfirmationStatus.AI_SUGGESTED
    assert questions.confirmation_status is ConfirmationStatus.AI_SUGGESTED
    confirmed = confirm_proposal(analysis)
    assert confirmed.confirmation_status is ConfirmationStatus.USER_CONFIRMED
    assert analysis.confirmation_status is ConfirmationStatus.AI_SUGGESTED


def test_no_evidence_cannot_become_completed() -> None:
    draft = CompletionEvaluationDraft(
        criterion_results=[
            CriterionEvaluationDraft(
                criterion_id=criterion.id,
                status=CriterionStatus.PASS,
                evidence=[],
                explanation="claimed pass",
            )
            for criterion in VERSION_V2.acceptance_criteria
        ],
        overall_status=CompletionStatus.COMPLETED,
        unresolved_items=[],
    )
    result = evaluate_completion_with_ai(
        VERSION_V2,
        EXECUTION_PLAN_V2,
        evidence_status=[],
        provider=QueueProvider(draft),
    )
    assert result.confirmation_status is ConfirmationStatus.AI_SUGGESTED
    assert result.payload.overall_status is CompletionStatus.BLOCKED_BY_MISSING_EVIDENCE
    assert all(
        item.status is CriterionStatus.MISSING_EVIDENCE
        for item in result.payload.criterion_results
    )
    assert set(result.payload.missing_evidence) == {
        criterion.id for criterion in VERSION_V2.acceptance_criteria
    }

