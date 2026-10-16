"""Generate a consulting approach from a human-confirmed requirement."""
from requirement_alignment.ai.provider import LLMProvider
from requirement_alignment.ai.schemas import Proposal
from requirement_alignment.approach import (
    ConsultingApproach, ConsultingApproachDraft, Workstream,
)
from requirement_alignment.models import RequirementVersion

APPROACH_PROMPT = """You are an agency consulting approach designer.
Use only the confirmed requirement provided. Produce a transparent proposed approach.
Choose methods and workstreams that directly serve the requirement's objective and scope.
Never invent market research, case results, KPI improvements, budget, dates or staffing.
If a timeline or any fact is unknown, use null or an explicit unknown.
All workstreams must list concrete deliverables and required input data.
Methods are recommendations, not proven findings.
Return JSON matching the schema. Human review is mandatory.
"""


def generate_consulting_approach(
    requirement: RequirementVersion, provider: LLMProvider
) -> Proposal[ConsultingApproach]:
    draft = provider.generate_structured(
        APPROACH_PROMPT, requirement.model_dump_json(), ConsultingApproachDraft
    )
    return Proposal(payload=ConsultingApproach(
        based_on_requirement_version_id=requirement.id,
        rationale=draft.rationale,
        workstreams=[Workstream(**w.model_dump()) for w in draft.workstreams],
        unknowns=draft.unknowns,
        proposed_timeline=draft.proposed_timeline,
    ))
