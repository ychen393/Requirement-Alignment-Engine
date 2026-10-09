"""LLM-facing draft schemas and application-level confirmation envelopes."""

from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from requirement_alignment.models import (
    CompletionStatus,
    CriterionStatus,
    DiffCategory,
    FieldType,
    MetricOperator,
    Priority,
)


class DraftModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ConfirmationStatus(str, Enum):
    AI_SUGGESTED = "AI_SUGGESTED"
    USER_CONFIRMED = "USER_CONFIRMED"


PayloadT = TypeVar("PayloadT")


class Proposal(BaseModel, Generic[PayloadT]):
    confirmation_status: ConfirmationStatus = ConfirmationStatus.AI_SUGGESTED
    payload: PayloadT


def confirm_proposal(proposal: Proposal[PayloadT]) -> Proposal[PayloadT]:
    return proposal.model_copy(update={"confirmation_status": ConfirmationStatus.USER_CONFIRMED})


class AnalysisItemDraft(DraftModel):
    description: str = Field(min_length=1)
    evidence: str | None = None
    affected_fields: list[str] = Field(default_factory=list)


class RiskDraft(AnalysisItemDraft):
    likelihood: Priority
    impact: Priority
    mitigation: str | None = None


class RequirementAnalysisDraft(DraftModel):
    confirmed_information: list[AnalysisItemDraft]
    missing_information: list[AnalysisItemDraft]
    assumptions: list[AnalysisItemDraft]
    ambiguities: list[AnalysisItemDraft]
    risks: list[RiskDraft]


class ClarificationQuestionDraft(DraftModel):
    question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    target_field: str = Field(min_length=1)
    priority: Priority = Priority.MEDIUM


class ClarificationQuestionsDraft(DraftModel):
    questions: list[ClarificationQuestionDraft]


class MetricDraft(DraftModel):
    name: str
    description: str
    measurement_method: str
    target_operator: MetricOperator
    target_value: float | str | list[float]
    unit: str | None = None


class AcceptanceCriterionDraft(DraftModel):
    title: str
    description: str
    verification_method: str
    metric_name: str | None = None
    required: bool = True
    evidence_requirements: list[str] = Field(min_length=1)


class RequirementFieldDraft(DraftModel):
    key: str
    label: str
    value: Any
    field_type: FieldType
    required: bool = False
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None


class RequirementVersionDraft(DraftModel):
    objective: str
    scope: list[str] = Field(min_length=1)
    out_of_scope: list[str]
    constraints: list[str]
    expected_outputs: list[str] = Field(min_length=1)
    metrics: list[MetricDraft]
    acceptance_criteria: list[AcceptanceCriterionDraft] = Field(min_length=1)
    additional_fields: list[RequirementFieldDraft] = Field(default_factory=list)
    change_summary: str | None = None


class TaskDraft(DraftModel):
    key: str = Field(min_length=1)
    source_task_id: UUID | None = None
    title: str
    description: str
    dependency_keys: list[str] = Field(default_factory=list)
    requirement_references: list[str] = Field(default_factory=list)
    acceptance_criterion_titles: list[str] = Field(default_factory=list)
    deliverable_keys: list[str] = Field(default_factory=list)
    estimated_effort_hours: float | None = Field(default=None, gt=0)
    execution_order: int = Field(ge=1)


class DeliverableDraft(DraftModel):
    key: str
    name: str
    description: str
    format: str
    task_keys: list[str]
    acceptance_criterion_titles: list[str] = Field(default_factory=list)


class ExecutionPlanDraft(DraftModel):
    objective: str
    tasks: list[TaskDraft] = Field(min_length=1)
    deliverables: list[DeliverableDraft] = Field(min_length=1)


class DiffEntryDraft(DraftModel):
    field_path: str
    category: DiffCategory
    old_value: Any = None
    new_value: Any = None
    explanation: str


class ImpactAction(str, Enum):
    KEEP = "KEEP"
    MODIFY = "MODIFY"
    REWORK = "REWORK"


class ExistingTaskDecisionDraft(DraftModel):
    task_id: UUID
    action: ImpactAction
    reason: str
    affected_requirement_paths: list[str] = Field(default_factory=list)
    recommended_action: str


class ChangeAnalysisDraft(DraftModel):
    next_requirement: RequirementVersionDraft
    diff_entries: list[DiffEntryDraft] = Field(min_length=1)
    task_decisions: list[ExistingTaskDecisionDraft]
    revised_plan: ExecutionPlanDraft
    impact_summary: str


class EvidenceItem(DraftModel):
    criterion_id: UUID
    status: str
    evidence: list[str] = Field(default_factory=list)
    observed_value: Any = None


class CriterionEvaluationDraft(DraftModel):
    criterion_id: UUID
    status: CriterionStatus
    evidence: list[str] = Field(default_factory=list)
    observed_value: Any = None
    explanation: str


class CompletionEvaluationDraft(DraftModel):
    criterion_results: list[CriterionEvaluationDraft]
    overall_status: CompletionStatus
    unresolved_items: list[str]

