"""Consulting proposal contracts: source-aware, renderer-independent drafts.

These models do not implement persistence, user authorization, or AI generation.
"""
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaimProvenance(str, Enum):
    CLIENT_EXPLICIT = "CLIENT_EXPLICIT"
    CONSULTANT_CONFIRMED = "CONSULTANT_CONFIRMED"
    SOURCE_DOCUMENT = "SOURCE_DOCUMENT"
    AI_INFERRED = "AI_INFERRED"
    UNKNOWN = "UNKNOWN"


class Claim(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    text: str = Field(min_length=1)
    provenance: ClaimProvenance
    source_refs: list[str] = Field(default_factory=list)
    explicit_assumption: bool = False

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.provenance is ClaimProvenance.SOURCE_DOCUMENT and not self.source_refs:
            raise ValueError("source document claim requires a reference")
        if self.provenance in (ClaimProvenance.AI_INFERRED, ClaimProvenance.UNKNOWN) and not self.explicit_assumption:
            raise ValueError("inferred and unknown claims must be marked as assumptions")
        return self


class ProposalSectionType(str, Enum):
    CONTEXT = "CONTEXT"
    UNDERSTANDING = "UNDERSTANDING"
    OBJECTIVES = "OBJECTIVES"
    APPROACH = "APPROACH"
    WORKSTREAMS = "WORKSTREAMS"
    DELIVERABLES = "DELIVERABLES"
    TIMELINE = "TIMELINE"
    ASSUMPTIONS = "ASSUMPTIONS"
    NEXT_STEPS = "NEXT_STEPS"


class ProposalBlockType(str, Enum):
    PARAGRAPH = "PARAGRAPH"
    BULLETS = "BULLETS"
    KEY_MESSAGE = "KEY_MESSAGE"


class ProposalBlock(StrictModel):
    type: ProposalBlockType
    text: str | None = None
    items: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_content(self):
        if self.type is ProposalBlockType.BULLETS and not self.items:
            raise ValueError("bullet blocks need items")
        if self.type is not ProposalBlockType.BULLETS and not (self.text and self.text.strip()):
            raise ValueError("text blocks need text")
        return self


class ProposalSection(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    type: ProposalSectionType
    heading: str = Field(min_length=1)
    blocks: list[ProposalBlock] = Field(min_length=1)
    claim_refs: list[UUID] = Field(default_factory=list)
    order: int = Field(ge=0)


class ProposalStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED_FOR_EXPORT = "APPROVED_FOR_EXPORT"


class ProposalDocument(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    based_on_requirement_version_id: UUID
    version_number: int = Field(ge=1)
    title: str = Field(min_length=1)
    executive_summary: str = Field(min_length=1)
    sections: list[ProposalSection] = Field(min_length=1)
    claims: list[Claim] = Field(default_factory=list)
    status: ProposalStatus = ProposalStatus.DRAFT

    @model_validator(mode="after")
    def validate_claim_references(self):
        ids = [c.id for c in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate claim IDs")
        if len({s.id for s in self.sections}) != len(self.sections):
            raise ValueError("duplicate section IDs")
        if len({s.order for s in self.sections}) != len(self.sections):
            raise ValueError("duplicate section order")
        referenced = {ref for section in self.sections for ref in section.claim_refs}
        if referenced - set(ids):
            raise ValueError("section references missing claims")
        if self.status is ProposalStatus.APPROVED_FOR_EXPORT:
            if any(c.provenance in (ClaimProvenance.AI_INFERRED, ClaimProvenance.UNKNOWN) and not c.explicit_assumption for c in self.claims):
                raise ValueError("unmarked inferred claims cannot be exported")
        return self
