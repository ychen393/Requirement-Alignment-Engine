"""Structured consulting workstreams, independent of execution staffing."""
from uuid import UUID, uuid4
from pydantic import Field, model_validator
from requirement_alignment.consulting import StrictModel


class Workstream(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    methods: list[str] = Field(min_length=1)
    activities: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(min_length=1)
    data_required: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ConsultingApproach(StrictModel):
    based_on_requirement_version_id: UUID
    rationale: str = Field(min_length=1)
    workstreams: list[Workstream] = Field(min_length=1)
    unknowns: list[str] = Field(default_factory=list)
    proposed_timeline: str | None = None

    @model_validator(mode="after")
    def check_uniqueness(self):
        ids = [w.id for w in self.workstreams]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate workstream IDs")
        return self


class WorkstreamDraft(StrictModel):
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    methods: list[str] = Field(min_length=1)
    activities: list[str] = Field(default_factory=list)
    deliverables: list[str] = Field(min_length=1)
    data_required: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class ConsultingApproachDraft(StrictModel):
    rationale: str = Field(min_length=1)
    workstreams: list[WorkstreamDraft] = Field(min_length=1)
    unknowns: list[str] = Field(default_factory=list)
    proposed_timeline: str | None = None
