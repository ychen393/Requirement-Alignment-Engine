"""Print the deterministic requirement-alignment workflow for a human reader."""

from pathlib import Path
import sys

# Allow `python demo.py` from a fresh checkout without requiring an editable install.
sys.path.insert(0, str(Path(__file__).parent / "src"))

from requirement_alignment.models import CriterionStatus, DiffCategory  # noqa: E402
from requirement_alignment.demo_data import (  # noqa: E402
    ANALYSIS,
    CLARIFICATION_QUESTIONS,
    COMPLETION_EVALUATION,
    DIFF,
    EXECUTION_PLAN,
    EXECUTION_PLAN_V2,
    IMPACT_ANALYSIS,
    RAW_REQUIREMENT,
    STAKEHOLDER_CHANGE_TEXT,
    VERSION_V1,
)


def bullet(items: list[str], marker: str = "-") -> None:
    for item in items:
        print(f"  {marker} {item}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("1. Original request")
    print(f"  {RAW_REQUIREMENT.description}\n")

    print("2. Missing information detected")
    bullet([item.description for item in ANALYSIS.missing_information])

    print("\n3. Clarification questions")
    bullet([f"{item.question} -> {item.answer}" for item in CLARIFICATION_QUESTIONS])

    print("\n4. Requirement V1")
    print(f"  Objective: {VERSION_V1.objective}")
    bullet(VERSION_V1.scope)

    print("\n5. New stakeholder request")
    print(f"  {STAKEHOLDER_CHANGE_TEXT}")

    print("\n6. V1 -> V2 changes")
    markers = {
        DiffCategory.ADDED: "+",
        DiffCategory.REMOVED: "-",
        DiffCategory.MODIFIED: "~",
        DiffCategory.UNCHANGED: "=",
    }
    for entry in DIFF.entries:
        print(f"  {markers[entry.category]} {entry.explanation}")

    print("\n7. Impact on existing work")
    print(f"  Before change: {len(EXECUTION_PLAN.tasks)} tasks")
    print(f"  ✓ Keep {len(IMPACT_ANALYSIS.valid_task_ids)} completed task(s)")
    bullet(
        [item.recommended_action for item in IMPACT_ANALYSIS.tasks_needing_modification],
        marker="△",
    )
    bullet([item.title for item in IMPACT_ANALYSIS.new_tasks_required], marker="+")
    print("  ✓ No completed output requires full rework")

    print(f"\n8. Current execution plan: {len(EXECUTION_PLAN_V2.tasks)} tasks")
    for task in EXECUTION_PLAN_V2.tasks:
        print(f"  {task.execution_order}. [{task.status.value}] {task.title}")

    print("\n9. Completion status")
    print(f"  {COMPLETION_EVALUATION.overall_status.value}")
    passed = [
        item.explanation
        for item in COMPLETION_EVALUATION.criterion_results
        if item.status is CriterionStatus.PASS
    ]
    print("  Passed:")
    bullet(passed, marker="✓")
    print("  Missing or incomplete:")
    bullet(COMPLETION_EVALUATION.unresolved_items, marker="!")
    print("  The work is not complete because required project evidence and final approval are missing.")


if __name__ == "__main__":
    main()
