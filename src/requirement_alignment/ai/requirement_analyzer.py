"""AI-assisted requirement analysis and proposal generation."""

from uuid import uuid4

from requirement_alignment.ai.prompts import (
    ANALYZE_REQUIREMENT_PROMPT,
    CLARIFICATION_PROMPT,
    REQUIREMENT_PROPOSAL_PROMPT,
)
from requirement_alignment.ai.provider import AIResponseValidationError, LLMProvider
from requirement_alignment.ai.schemas import (
    ClarificationQuestionsDraft,
    Proposal,
    RequirementAnalysisDraft,
    RequirementVersionDraft,
)
from requirement_alignment.models import (
    AcceptanceCriterion,
    AnalysisItem,
    ClarificationQuestion,
    Metric,
    QuestionStatus,
    RawRequirement,
    RequirementAnalysis,
    RequirementField,
    RequirementVersion,
    RiskItem,
)
from requirement_alignment.services import analyze_raw_requirement, create_requirement_version


def analyze_requirement_with_ai(
    raw_requirement: RawRequirement,
    provider: LLMProvider,
) -> Proposal[RequirementAnalysis]:
    draft = provider.generate_structured(
        ANALYZE_REQUIREMENT_PROMPT,
        raw_requirement.model_dump_json(),
        RequirementAnalysisDraft,
    )
    analysis = analyze_raw_requirement(
        raw_requirement,
        confirmed_information=[AnalysisItem(**item.model_dump()) for item in draft.confirmed_information],
        missing_information=[AnalysisItem(**item.model_dump()) for item in draft.missing_information],
        assumptions=[AnalysisItem(**item.model_dump()) for item in draft.assumptions],
        ambiguities=[AnalysisItem(**item.model_dump()) for item in draft.ambiguities],
        risks=[RiskItem(**item.model_dump()) for item in draft.risks],
    )
    return Proposal(payload=analysis)


def generate_clarification_questions_with_ai(
    raw_requirement: RawRequirement,
    analysis: RequirementAnalysis,
    provider: LLMProvider,
) -> Proposal[list[ClarificationQuestion]]:
    draft = provider.generate_structured(
        CLARIFICATION_PROMPT,
        f"Raw requirement:\n{raw_requirement.model_dump_json()}\nAnalysis:\n{analysis.model_dump_json()}",
        ClarificationQuestionsDraft,
    )
    questions = [
        ClarificationQuestion(
            analysis_id=analysis.id,
            question=item.question,
            rationale=item.rationale,
            target_field=item.target_field,
            priority=item.priority,
            status=QuestionStatus.OPEN,
        )
        for item in draft.questions
    ]
    return Proposal(payload=questions)


def materialize_requirement_draft(
    raw_requirement: RawRequirement,
    draft: RequirementVersionDraft,
    *,
    version_number: int,
    previous_version: RequirementVersion | None = None,
) -> RequirementVersion:
    metrics = [Metric(**item.model_dump()) for item in draft.metrics]
    metric_ids_by_name = {metric.name: metric.id for metric in metrics}
    if len(metric_ids_by_name) != len(metrics):
        raise AIResponseValidationError("AI proposed duplicate metric names")
    criteria: list[AcceptanceCriterion] = []
    for item in draft.acceptance_criteria:
        if item.metric_name and item.metric_name not in metric_ids_by_name:
            raise AIResponseValidationError(
                f"Acceptance criterion references unknown metric: {item.metric_name}"
            )
        values = item.model_dump(exclude={"metric_name"})
        values["metric_id"] = metric_ids_by_name.get(item.metric_name)
        criteria.append(AcceptanceCriterion(**values))
    additional_fields = [RequirementField(**item.model_dump()) for item in draft.additional_fields]
    return create_requirement_version(
        raw_requirement,
        id=uuid4(),
        version_number=version_number,
        previous_version=previous_version,
        objective=draft.objective,
        scope=draft.scope,
        out_of_scope=draft.out_of_scope,
        constraints=draft.constraints,
        expected_outputs=draft.expected_outputs,
        metrics=metrics,
        acceptance_criteria=criteria,
        additional_fields=additional_fields,
        created_by="AI proposal",
        change_summary=draft.change_summary,
    )


def generate_requirement_proposal_with_ai(
    raw_requirement: RawRequirement,
    analysis: RequirementAnalysis,
    answered_questions: list[ClarificationQuestion],
    provider: LLMProvider,
) -> Proposal[RequirementVersion]:
    if any(question.status is not QuestionStatus.ANSWERED for question in answered_questions):
        raise ValueError("all supplied clarification questions must be answered")
    draft = provider.generate_structured(
        REQUIREMENT_PROPOSAL_PROMPT,
        "\n".join(
            [
                f"Raw requirement: {raw_requirement.model_dump_json()}",
                f"Analysis: {analysis.model_dump_json()}",
                "Answered clarification questions:",
                *[question.model_dump_json() for question in answered_questions],
            ]
        ),
        RequirementVersionDraft,
    )
    return Proposal(payload=materialize_requirement_draft(raw_requirement, draft, version_number=1))

