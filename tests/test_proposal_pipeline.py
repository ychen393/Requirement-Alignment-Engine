"""Pure end-to-end contract -> composition -> HTML rendering checks."""
from uuid import uuid4
import pytest
from pydantic import ValidationError
from requirement_alignment.approach import ConsultingApproach, Workstream
from requirement_alignment.consulting import ProposalStatus
from requirement_alignment.proposal_generator import generate_proposal
from requirement_alignment.html_renderer import render_proposal_html
from tests.fixtures.model_benchmarking import VERSION_V1


def approach():
    return ConsultingApproach(
        based_on_requirement_version_id=VERSION_V1.id,
        rationale="Analyze candidate models within the agreed evaluation scope.",
        workstreams=[Workstream(
            title="Evaluation",
            objective="Assess model capabilities",
            methods=["Benchmark evaluation"],
            deliverables=["Comparison report"],
            data_required=["Test cases"],
        )],
        unknowns=["Budget not provided"],
    )


def test_confirmed_requirement_to_proposal_to_safe_preview():
    proposal = generate_proposal(VERSION_V1, approach(), project_id=uuid4())
    assert proposal.status is ProposalStatus.REVIEW_REQUIRED
    html = render_proposal_html(proposal, allow_draft_preview=True)
    assert "<!doctype html>" in html
    assert "DRAFT PREVIEW" in html
    assert "Comparison report" in html
    assert "Budget not provided" in html
    assert str(VERSION_V1.id) in html


def test_export_rejects_unreviewed_draft():
    proposal = generate_proposal(VERSION_V1, approach(), project_id=uuid4())
    with pytest.raises(ValueError, match="approved"):
        render_proposal_html(proposal)


def test_approach_must_match_requirement_version():
    other = approach().model_copy(update={"based_on_requirement_version_id": uuid4()})
    with pytest.raises(ValueError, match="confirmed requirement"):
        generate_proposal(VERSION_V1, other, project_id=uuid4())


def test_html_escapes_user_controlled_content():
    altered = VERSION_V1.model_copy(update={"objective": '<script>alert("pwn")</script>'})
    a = approach().model_copy(update={"based_on_requirement_version_id": altered.id})
    proposal = generate_proposal(altered, a, project_id=uuid4())
    html = render_proposal_html(proposal, allow_draft_preview=True)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
