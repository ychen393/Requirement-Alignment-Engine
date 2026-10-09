"""Requirement change, diff, and impact contracts."""

from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from requirement_alignment.models.common import (
    DiffCategory,
    DomainModel,
    IdentifiedModel,
    UTCDateTime,
    utc_now,
)
from requirement_alignment.models.planning import Task


class RequirementChange(IdentifiedModel):
    from_version_id: UUID
    requested_by: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    requested_changes: list[str] = Field(min_length=1)
    requested_at: UTCDateTime = Field(default_factory=utc_now)
    resulting_version_id: UUID


class RequirementDiffEntry(IdentifiedModel):
    field_path: str = Field(min_length=1)
    category: DiffCategory
    old_value: Any = None
    new_value: Any = None
    explanation: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_values_for_category(self) -> "RequirementDiffEntry":
        if self.category is DiffCategory.ADDED and self.new_value is None:
            raise ValueError("ADDED entries require a new value")
        if self.category is DiffCategory.REMOVED and self.old_value is None:
            raise ValueError("REMOVED entries require an old value")
        if self.category in {DiffCategory.MODIFIED, DiffCategory.UNCHANGED}:
            if self.old_value is None or self.new_value is None:
                raise ValueError(f"{self.category.value} entries require old and new values")
        if self.category is DiffCategory.MODIFIED and self.old_value == self.new_value:
            raise ValueError("MODIFIED entries must contain different values")
        if self.category is DiffCategory.UNCHANGED and self.old_value != self.new_value:
            raise ValueError("UNCHANGED entries must contain equal values")
        return self


class RequirementDiff(IdentifiedModel):
    from_version_id: UUID
    to_version_id: UUID
    entries: list[RequirementDiffEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def versions_must_differ(self) -> "RequirementDiff":
        if self.from_version_id == self.to_version_id:
            raise ValueError("diff versions must differ")
        return self

    def entries_for(self, category: DiffCategory) -> list[RequirementDiffEntry]:
        return [entry for entry in self.entries if entry.category is category]

    @property
    def added(self) -> list[RequirementDiffEntry]:
        return self.entries_for(DiffCategory.ADDED)

    @property
    def removed(self) -> list[RequirementDiffEntry]:
        return self.entries_for(DiffCategory.REMOVED)

    @property
    def modified(self) -> list[RequirementDiffEntry]:
        return self.entries_for(DiffCategory.MODIFIED)

    @property
    def unchanged(self) -> list[RequirementDiffEntry]:
        return self.entries_for(DiffCategory.UNCHANGED)


class TaskImpact(DomainModel):
    task_id: UUID
    reason: str = Field(min_length=1)
    affected_requirement_paths: list[str] = Field(default_factory=list)
    recommended_action: str = Field(min_length=1)


class ImpactAnalysis(IdentifiedModel):
    requirement_diff_id: UUID
    valid_task_ids: list[UUID] = Field(default_factory=list)
    tasks_needing_modification: list[TaskImpact] = Field(default_factory=list)
    tasks_requiring_rework: list[TaskImpact] = Field(default_factory=list)
    new_tasks_required: list[Task] = Field(default_factory=list)
    affected_deliverable_ids: list[UUID] = Field(default_factory=list)
    affected_criterion_ids: list[UUID] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    analyzed_at: UTCDateTime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def task_categories_must_not_overlap(self) -> "ImpactAnalysis":
        groups = [
            set(self.valid_task_ids),
            {item.task_id for item in self.tasks_needing_modification},
            {item.task_id for item in self.tasks_requiring_rework},
            {item.id for item in self.new_tasks_required},
        ]
        for index, group in enumerate(groups):
            for other in groups[index + 1 :]:
                if group & other:
                    raise ValueError("task impact categories must not overlap")
        return self
