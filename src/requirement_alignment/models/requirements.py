"""Raw, analyzed, and versioned requirement contracts."""

from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from requirement_alignment.models.common import (
    DomainModel,
    FieldType,
    IdentifiedModel,
    MetricOperator,
    Priority,
    TimestampedModel,
    UTCDateTime,
    WorkflowState,
    utc_now,
)


class RawRequirement(TimestampedModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    submitted_by: str = Field(min_length=1)
    source: str = Field(min_length=1)
    status: WorkflowState = WorkflowState.DRAFT


class AnalysisItem(IdentifiedModel):
    description: str = Field(min_length=1)
    evidence: str | None = None
    affected_fields: list[str] = Field(default_factory=list)


class RiskItem(AnalysisItem):
    likelihood: Priority
    impact: Priority
    mitigation: str | None = None


class RequirementAnalysis(IdentifiedModel):
    raw_requirement_id: UUID
    confirmed_information: list[AnalysisItem] = Field(default_factory=list)
    missing_information: list[AnalysisItem] = Field(default_factory=list)
    assumptions: list[AnalysisItem] = Field(default_factory=list)
    ambiguities: list[AnalysisItem] = Field(default_factory=list)
    risks: list[RiskItem] = Field(default_factory=list)
    analyzed_at: UTCDateTime = Field(default_factory=utc_now)


class RequirementField(IdentifiedModel):
    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: Any
    field_type: FieldType
    required: bool = False
    source: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    notes: str | None = None


class Metric(IdentifiedModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    measurement_method: str = Field(min_length=1)
    target_operator: MetricOperator
    target_value: float | str | list[float]
    unit: str | None = None

    @model_validator(mode="after")
    def validate_between_target(self) -> "Metric":
        if self.target_operator is MetricOperator.BETWEEN:
            if not isinstance(self.target_value, list) or len(self.target_value) != 2:
                raise ValueError("BETWEEN metrics require exactly two target values")
            if self.target_value[0] > self.target_value[1]:
                raise ValueError("BETWEEN metric bounds must be ordered")
        return self


class AcceptanceCriterion(IdentifiedModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    verification_method: str = Field(min_length=1)
    metric_id: UUID | None = None
    required: bool = True
    evidence_requirements: list[str] = Field(min_length=1)


class RequirementVersion(TimestampedModel):
    raw_requirement_id: UUID
    version_number: int = Field(ge=1)
    previous_version_id: UUID | None = None
    objective: str = Field(min_length=1)
    scope: list[str] = Field(min_length=1)
    out_of_scope: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(min_length=1)
    metrics: list[Metric] = Field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = Field(min_length=1)
    additional_fields: list[RequirementField] = Field(default_factory=list)
    created_by: str = Field(min_length=1)
    change_summary: str | None = None
    is_current: bool = True

    @property
    def label(self) -> str:
        return f"V{self.version_number}"

    @model_validator(mode="after")
    def validate_local_references_and_keys(self) -> "RequirementVersion":
        metric_ids = [metric.id for metric in self.metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("metric IDs must be unique within a version")
        criterion_ids = [criterion.id for criterion in self.acceptance_criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("acceptance criterion IDs must be unique within a version")
        unknown_metrics = {
            criterion.metric_id
            for criterion in self.acceptance_criteria
            if criterion.metric_id is not None and criterion.metric_id not in metric_ids
        }
        if unknown_metrics:
            raise ValueError("acceptance criteria reference metrics outside this version")
        keys = [field.key for field in self.additional_fields]
        if len(keys) != len(set(keys)):
            raise ValueError("additional field keys must be unique within a version")
        return self
