"""Execution planning contracts."""

from uuid import UUID

from pydantic import Field, model_validator

from requirement_alignment.models.common import (
    DeliverableStatus,
    IdentifiedModel,
    TaskStatus,
    TimestampedModel,
)


class Task(IdentifiedModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: TaskStatus = TaskStatus.NOT_STARTED
    dependencies: list[UUID] = Field(default_factory=list)
    requirement_references: list[str] = Field(default_factory=list)
    acceptance_criterion_ids: list[UUID] = Field(default_factory=list)
    deliverable_ids: list[UUID] = Field(default_factory=list)
    estimated_effort_hours: float | None = Field(default=None, gt=0)
    execution_order: int = Field(ge=1)

    @model_validator(mode="after")
    def reject_self_dependency(self) -> "Task":
        if self.id in self.dependencies:
            raise ValueError("a task cannot depend on itself")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("task dependencies must be unique")
        return self


class Deliverable(IdentifiedModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    format: str = Field(min_length=1)
    task_ids: list[UUID] = Field(default_factory=list)
    acceptance_criterion_ids: list[UUID] = Field(default_factory=list)
    evidence_uri: str | None = None
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED


class ExecutionPlan(TimestampedModel):
    requirement_version_id: UUID
    objective: str = Field(min_length=1)
    tasks: list[Task] = Field(min_length=1)
    deliverables: list[Deliverable] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_plan_references(self) -> "ExecutionPlan":
        task_ids = [task.id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise ValueError("task IDs must be unique within a plan")
        known_tasks = set(task_ids)
        for task in self.tasks:
            if unknown := set(task.dependencies) - known_tasks:
                raise ValueError(f"task has dependencies outside this plan: {unknown}")
        deliverable_ids = [deliverable.id for deliverable in self.deliverables]
        if len(deliverable_ids) != len(set(deliverable_ids)):
            raise ValueError("deliverable IDs must be unique within a plan")
        known_deliverables = set(deliverable_ids)
        for task in self.tasks:
            if set(task.deliverable_ids) - known_deliverables:
                raise ValueError("task references a deliverable outside this plan")
        for deliverable in self.deliverables:
            if set(deliverable.task_ids) - known_tasks:
                raise ValueError("deliverable references a task outside this plan")
        return self

