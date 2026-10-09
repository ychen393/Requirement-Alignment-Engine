import pytest
from pydantic import ValidationError

from requirement_alignment.ai import ConfirmationStatus, Proposal, confirm_proposal
from requirement_alignment.api.main import ConfirmationRequiredError, create_app
from requirement_alignment.api.schemas import (
    AnalyzeRequest,
    AppMode,
    ChangeRequest,
    CompletionRequest,
    PlanRequest,
)
from tests.fixtures.model_benchmarking import (
    EXECUTION_PLAN,
    EXECUTION_PLAN_V2,
    RAW_REQUIREMENT,
    STAKEHOLDER_CHANGE_TEXT,
    VERSION_V1,
    VERSION_V2,
)


def endpoint(app, path: str):
    return next(route.endpoint for route in app.routes if getattr(route, "path", None) == path)


def test_api_exposes_expected_contracts_and_explicit_demo_mode() -> None:
    app = create_app(mode=AppMode.DEMO)
    paths = set(app.openapi()["paths"])
    assert {
        "/requirements/analyze",
        "/requirements/align",
        "/plans/generate",
        "/changes/analyze",
        "/completion/evaluate",
    } <= paths
    response = endpoint(app, "/requirements/analyze")(
        AnalyzeRequest(request=RAW_REQUIREMENT.description)
    )
    assert response.mode is AppMode.DEMO
    assert response.raw_requirement.confirmation_status is ConfirmationStatus.USER_CONFIRMED
    assert response.analysis.confirmation_status is ConfirmationStatus.AI_SUGGESTED


def test_plan_endpoint_requires_explicit_human_confirmation() -> None:
    app = create_app(mode=AppMode.DEMO)
    plan_endpoint = endpoint(app, "/plans/generate")
    suggested = Proposal(payload=VERSION_V1)
    with pytest.raises(ConfirmationRequiredError, match="USER_CONFIRMED"):
        plan_endpoint(PlanRequest(requirement=suggested))
    response = plan_endpoint(PlanRequest(requirement=confirm_proposal(suggested)))
    assert response.proposal.payload.id == EXECUTION_PLAN.id
    assert response.proposal.confirmation_status is ConfirmationStatus.AI_SUGGESTED


def test_change_and_completion_require_confirmed_current_state() -> None:
    app = create_app(mode=AppMode.DEMO)
    change_endpoint = endpoint(app, "/changes/analyze")
    with pytest.raises(ConfirmationRequiredError):
        change_endpoint(
            ChangeRequest(
                raw_requirement=RAW_REQUIREMENT,
                current_requirement=Proposal(payload=VERSION_V1),
                current_plan=Proposal(payload=EXECUTION_PLAN),
                stakeholder_change=STAKEHOLDER_CHANGE_TEXT,
            )
        )
    change_response = change_endpoint(
        ChangeRequest(
            raw_requirement=RAW_REQUIREMENT,
            current_requirement=confirm_proposal(Proposal(payload=VERSION_V1)),
            current_plan=confirm_proposal(Proposal(payload=EXECUTION_PLAN)),
            stakeholder_change=STAKEHOLDER_CHANGE_TEXT,
        )
    )
    assert change_response.proposal.payload.revised_execution_plan.id == EXECUTION_PLAN_V2.id

    completion_endpoint = endpoint(app, "/completion/evaluate")
    completion_response = completion_endpoint(
        CompletionRequest(
            current_requirement=confirm_proposal(Proposal(payload=VERSION_V2)),
            current_plan=confirm_proposal(Proposal(payload=EXECUTION_PLAN_V2)),
            evidence_status=[],
        )
    )
    assert completion_response.proposal.payload.execution_plan_id == EXECUTION_PLAN_V2.id
    assert completion_response.proposal.confirmation_status is ConfirmationStatus.AI_SUGGESTED


def test_api_rejects_unknown_request_fields() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(request="valid", unexpected=True)

