"""Proposal API contract and draft export safeguards."""
from uuid import uuid4
import pytest
from requirement_alignment.api.main import (
    ProposalGenerateRequest, ProposalRenderRequest, ConfirmationRequiredError, create_app,
)
from requirement_alignment.api.schemas import AppMode
from requirement_alignment.ai.schemas import Proposal, confirm_proposal
from requirement_alignment.approach import ConsultingApproach, Workstream
from tests.fixtures.model_benchmarking import VERSION_V1


def endpoint(app, path):
    return next(r.endpoint for r in app.routes if getattr(r, "path", None) == path)


def sample_approach():
    return ConsultingApproach(
        based_on_requirement_version_id=VERSION_V1.id, rationale="Check the agreed scope.",
        workstreams=[Workstream(
            title="Analysis", objective="Investigate", methods=["Review"],
            deliverables=["Summary"],
        )],
    )


def test_api_requires_confirmed_requirement_and_supports_rendering():
    app = create_app(mode=AppMode.DEMO)
    generate = endpoint(app, "/consulting/proposal")
    project = uuid4()
    with pytest.raises(ConfirmationRequiredError):
        generate(ProposalGenerateRequest(
            project_id=project, requirement=Proposal(payload=VERSION_V1),
            approach=sample_approach(),
        ))
    doc = generate(ProposalGenerateRequest(
        project_id=project,
        requirement=confirm_proposal(Proposal(payload=VERSION_V1)),
        approach=sample_approach(),
    ))
    assert doc.project_id == project
    preview = endpoint(app, "/consulting/proposal/preview")(
        ProposalRenderRequest(proposal=doc)
    )
    assert "DRAFT PREVIEW" in preview.body.decode()
    assert preview.headers["cache-control"] == "no-store"
    download = endpoint(app, "/consulting/proposal/export")(
        ProposalRenderRequest(proposal=doc)
    )
    assert "proposal-DRAFT.html" in download.headers["content-disposition"]
    assert "DRAFT PREVIEW" in download.body.decode()


def test_proposal_routes_in_openapi():
    paths = create_app(mode=AppMode.DEMO).openapi()["paths"]
    assert {"/consulting/proposal", "/consulting/proposal/preview",
            "/consulting/proposal/export"} <= set(paths)
