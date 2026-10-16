"""The consulting endpoint requires an explicitly confirmed requirement."""
import pytest
from requirement_alignment.ai.schemas import Proposal, confirm_proposal, ConfirmationStatus
from requirement_alignment.api.main import (
    ApproachRequest, ConfirmationRequiredError, create_app,
)
from requirement_alignment.api.schemas import AppMode
from tests.fixtures.model_benchmarking import VERSION_V1


def endpoint(app, path):
    return next(r.endpoint for r in app.routes if getattr(r, "path", None) == path)


def test_consulting_approach_endpoint_never_accepts_unconfirmed_requirement():
    app = create_app(mode=AppMode.DEMO)
    fn = endpoint(app, "/consulting/approach")
    with pytest.raises(ConfirmationRequiredError):
        fn(ApproachRequest(requirement=Proposal(payload=VERSION_V1)))


def test_consulting_approach_demo_returns_labeled_suggestion():
    app = create_app(mode=AppMode.DEMO)
    fn = endpoint(app, "/consulting/approach")
    out = fn(ApproachRequest(requirement=confirm_proposal(Proposal(payload=VERSION_V1))))
    assert out.mode is AppMode.DEMO
    assert out.proposal.confirmation_status is ConfirmationStatus.AI_SUGGESTED
    assert out.proposal.payload.based_on_requirement_version_id == VERSION_V1.id
    assert "DEMO ONLY" in out.proposal.payload.rationale
    assert "/consulting/approach" in app.openapi()["paths"]
