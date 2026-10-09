"""Manual smoke test for raw request -> analysis -> clarification questions."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from requirement_alignment.ai import (  # noqa: E402
    OpenAICompatibleProvider,
    analyze_requirement_with_ai,
    generate_clarification_questions_with_ai,
)
from requirement_alignment.models import RawRequirement, WorkflowState  # noqa: E402


REQUEST = "测试不同模型的能力评分，看看哪个模型比较适合我们的业务。"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["AI", "DEMO"])
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.mode == "DEMO":
        from requirement_alignment.demo_data import (
            ANALYSIS,
            CLARIFICATION_QUESTIONS,
            RAW_REQUIREMENT,
        )

        raw, analysis, questions = RAW_REQUIREMENT, ANALYSIS, CLARIFICATION_QUESTIONS
    else:
        raw = RawRequirement(
            title="模型能力评测",
            description=REQUEST,
            submitted_by="smoke-test user",
            source="manual smoke test",
            status=WorkflowState.NEEDS_CLARIFICATION,
        )
        provider = OpenAICompatibleProvider.from_env()
        analysis = analyze_requirement_with_ai(raw, provider).payload
        questions = generate_clarification_questions_with_ai(raw, analysis, provider).payload

    print(f"Mode: {args.mode}")
    print(f"Raw request: {raw.description}")
    print("\nDetected missing information:")
    for item in analysis.missing_information:
        print(f"- {item.description}")
    print("\nClarification questions (AI suggestions; user answers required):")
    for question in questions:
        print(f"- {question.question}")


if __name__ == "__main__":
    main()
