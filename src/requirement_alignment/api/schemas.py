"""HTTP request and response contracts."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from requirement_alignment.ai.change_analyzer import ChangeProposalBundle
from requirement_alignment.ai.schemas import EvidenceItem, Proposal
from requirement_alignment.models import (
    ClarificationQuestion,
    CompletionEvaluation,
    ExecutionPlan,
    RawRequirement,
    RequirementAnalysis,
    RequirementVersion,
)


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AppMode(str, Enum):
    AI = "AI"
    DEMO = "DEMO"


class AnalyzeRequest(APIModel):
    request: str = Field(min_length=1)
    title: str = "Requirement"
    submitted_by: str = "user"
    source: str = "api"


class AnalyzeResponse(APIModel):
    mode: AppMode
    raw_requirement: Proposal[RawRequirement]
    analysis: Proposal[RequirementAnalysis]
    clarification_questions: Proposal[list[ClarificationQuestion]]


class AlignRequest(APIModel):
    raw_requirement: RawRequirement
    analysis: RequirementAnalysis
    answered_clarification_questions: list[ClarificationQuestion]


class RequirementProposalResponse(APIModel):
    mode: AppMode
    proposal: Proposal[RequirementVersion]


class PlanRequest(APIModel):
    requirement: Proposal[RequirementVersion]


class PlanProposalResponse(APIModel):
    mode: AppMode
    proposal: Proposal[ExecutionPlan]


class ChangeRequest(APIModel):
    raw_requirement: RawRequirement
    current_requirement: Proposal[RequirementVersion]
    current_plan: Proposal[ExecutionPlan]
    stakeholder_change: str = Field(min_length=1)


class ChangeProposalResponse(APIModel):
    mode: AppMode
    proposal: Proposal[ChangeProposalBundle]


class CompletionRequest(APIModel):
    current_requirement: Proposal[RequirementVersion]
    current_plan: Proposal[ExecutionPlan]
    evidence_status: list[EvidenceItem]


class CompletionProposalResponse(APIModel):
    mode: AppMode
    proposal: Proposal[CompletionEvaluation]


class StatusResponse(APIModel):
    mode: AppMode | None
    status: str

