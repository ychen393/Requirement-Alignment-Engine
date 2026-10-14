"""Deterministic first-draft proposal composer.

No LLM or external data access: every section derives from the supplied confirmed
requirement and explicit proposed approach. A draft is NOT client-approved.
"""
from uuid import UUID
from requirement_alignment.approach import ConsultingApproach
from requirement_alignment.consulting import (
    Claim, ClaimProvenance, ProposalBlock, ProposalBlockType,
    ProposalDocument, ProposalSection, ProposalSectionType, ProposalStatus,
)
from requirement_alignment.models import RequirementVersion


def generate_proposal(
    requirement: RequirementVersion, approach: ConsultingApproach, *, project_id: UUID
) -> ProposalDocument:
    if approach.based_on_requirement_version_id != requirement.id:
        raise ValueError("approach must refer to this confirmed requirement version")

    claims = [
        Claim(text=requirement.objective, provenance=ClaimProvenance.CONSULTANT_CONFIRMED),
    ]
    def section(kind, heading, paragraphs=(), bullets=(), claim_refs=()):
        blocks = [ProposalBlock(type=ProposalBlockType.PARAGRAPH, text=p) for p in paragraphs if p]
        if bullets:
            blocks.append(ProposalBlock(type=ProposalBlockType.BULLETS, items=list(bullets)))
        if not blocks:
            blocks = [ProposalBlock(type=ProposalBlockType.PARAGRAPH, text="To be agreed with the client.")]
        sections.append(ProposalSection(
            type=kind, heading=heading, blocks=blocks, claim_refs=list(claim_refs),
            order=len(sections),
        ))

    sections = []
    section(ProposalSectionType.UNDERSTANDING, "Our understanding",
            paragraphs=[requirement.objective], claim_refs=[claims[0].id])
    section(ProposalSectionType.OBJECTIVES, "Project objectives",
            bullets=[requirement.objective, *requirement.scope],
            claim_refs=[claims[0].id])
    section(ProposalSectionType.APPROACH, "Proposed approach",
            paragraphs=[approach.rationale, "The following methods are proposals, not research findings."])
    for workstream in approach.workstreams:
        section(ProposalSectionType.WORKSTREAMS, workstream.title,
                paragraphs=[workstream.objective],
                bullets=[*"Methods: " + m for m in workstream.methods] +
                [*"Data required: " + d for d in workstream.data_required])
    outputs = list(dict.fromkeys(
        [*requirement.expected_outputs, *(d for w in approach.workstreams for d in w.deliverables)]
    ))
    section(ProposalSectionType.DELIVERABLES, "Proposed deliverables", bullets=outputs)
    if approach.proposed_timeline:
        section(ProposalSectionType.TIMELINE, "Indicative timeline",
                paragraphs=[approach.proposed_timeline, "Subject to client confirmation."])
    unknowns = list(dict.fromkeys([*approach.unknowns, *(a for w in approach.workstreams for a in w.assumptions)]))
    section(ProposalSectionType.ASSUMPTIONS, "Assumptions and open questions",
            bullets=unknowns or ["Final scope and commercial terms remain subject to review."])
    section(ProposalSectionType.NEXT_STEPS, "Next steps",
            paragraphs=["Review the assumptions, confirm scope and agree next steps."])
    return ProposalDocument(
        project_id=project_id, based_on_requirement_version_id=requirement.id,
        version_number=1, title=f"Proposal: {requirement.objective}",
        executive_summary=("Draft approach for discussion. This proposal reflects the "
                           "confirmed requirement and recommended workstreams; "
                           "it does not claim research has been performed."),
        sections=sections, claims=claims, status=ProposalStatus.REVIEW_REQUIRED,
    )
