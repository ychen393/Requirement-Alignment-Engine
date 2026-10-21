"""Tests for renderer-independent consulting proposal contracts."""
from uuid import uuid4
import pytest
from pydantic import ValidationError

from requirement_alignment.consulting import (
    Claim, ClaimProvenance, ProposalBlock, ProposalBlockType,
    ProposalDocument, ProposalSection, ProposalSectionType,
)


def example_proposal():
    claim = Claim(text="Skincare brand is exploring Xiaohongshu.", provenance=ClaimProvenance.CLIENT_EXPLICIT)
    section = ProposalSection(
        type=ProposalSectionType.UNDERSTANDING,
        heading="Our understanding",
        blocks=[ProposalBlock(type=ProposalBlockType.PARAGRAPH, text="Our understanding is provisional.")],
        claim_refs=[claim.id], order=0,
    )
    return dict(project_id=uuid4(), based_on_requirement_version_id=uuid4(),
                version_number=1, title="Proposal", executive_summary="For client review.",
                sections=[section], claims=[claim])


def test_proposal_uses_explicit_claim_references():
    proposal = ProposalDocument(**example_proposal())
    assert proposal.sections[0].claim_refs[0] == proposal.claims[0].id


def test_unknown_claim_refs_are_rejected():
    data = example_proposal()
    data["sections"][0] = data["sections"][0].model_copy(update={"claim_refs": [uuid4()]})
    with pytest.raises(ValidationError, match="missing claims"):
        ProposalDocument(**data)


def test_source_claim_must_have_reference():
    with pytest.raises(ValidationError, match="requires a reference"):
        Claim(text="Benchmark increased by 30%", provenance=ClaimProvenance.SOURCE_DOCUMENT)


def test_ai_inferred_claim_must_be_explicitly_labeled():
    with pytest.raises(ValidationError, match="marked as assumptions"):
        Claim(text="Audience is 18-24", provenance=ClaimProvenance.AI_INFERRED)
    assert Claim(text="Audience might be 18-24", provenance=ClaimProvenance.AI_INFERRED,
                 explicit_assumption=True).explicit_assumption


def test_bullets_need_items():
    with pytest.raises(ValidationError, match="need items"):
        ProposalBlock(type=ProposalBlockType.BULLETS, items=[])
