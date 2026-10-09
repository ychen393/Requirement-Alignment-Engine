from uuid import uuid4

import pytest
from pydantic import ValidationError

from requirement_alignment.models import ExecutionPlan, Task
from tests.fixtures.model_benchmarking import EXECUTION_PLAN, VERSION_V1


def test_execution_plan_dependencies_are_valid() -> None:
    task_ids = {task.id for task in EXECUTION_PLAN.tasks}
    assert all(set(task.dependencies) <= task_ids for task in EXECUTION_PLAN.tasks)


def test_task_rejects_self_dependency() -> None:
    task_id = uuid4()
    with pytest.raises(ValidationError, match="cannot depend on itself"):
        Task(
            id=task_id,
            title="Invalid",
            description="Self-dependent task",
            dependencies=[task_id],
            execution_order=1,
        )


def test_plan_rejects_dependency_outside_plan() -> None:
    with pytest.raises(ValidationError, match="outside this plan"):
        ExecutionPlan(
            requirement_version_id=VERSION_V1.id,
            objective="Invalid plan",
            tasks=[
                Task(
                    title="Orphan",
                    description="Depends on absent task",
                    dependencies=[uuid4()],
                    execution_order=1,
                )
            ],
            deliverables=EXECUTION_PLAN.deliverables,
        )

