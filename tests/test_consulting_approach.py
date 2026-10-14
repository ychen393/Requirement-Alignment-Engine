"""Contract and generation tests; no network/model access required."""
from uuid import uuid4
import pytest
from pydantic import ValidationError
from requirement_alignment.approach import (
    ConsultingApproach, ConsultingApproachDraft, Workstream,
)
from requirement_alignment.ai.approach_generator import generate_consulting_approach
from requirement_alignment.ai.schemas import ConfirmationStatus
from tests.fixtures.model_benchmarking import VERSION_V1


class StubProvider:
    def generate_structured(self, system_prompt, user_prompt, response_model):
        assert "Never invent" in system_prompt
        assert str(VERSION_V1.id) in user_prompt
        assert response_model is ConsultingApproachDraft
        return ConsultingApproachDraft(
            rationale="Compare model capabilities against defined criteria.",
            workstreams=[dict(
                title="Evaluate candidates",
                objective="Compare capabilities",
                methods=["Controlled evaluation"],
                deliverables=["Evaluation report"],
                data_required=["Approved test cases"],
            )],
            unknowns=["Budget not specified"],
        )


def test_approach_binds_to_confirmed_requirement_version():
    proposal = generate_consulting_approach(VERSION_V1, StubProvider())
    assert proposal.confirmation_status is ConfirmationStatus.AI_SUGGESTED
    assert proposal.payload.based_on_requirement_version_id == VERSION_V1.id
    assert proposal.payload.proposed_timeline is None
    assert proposal.payload.workstreams[0].deliverables == ["Evaluation report"]


def test_workstream_requires_actual_method_and_deliverable():
    with pytest.raises(ValidationError):
        Workstream(title="Empty", objective="Growth", methods=[], deliverables=[])


def test_workstream_ids_unique():
    w = Workstream(title="Research", objective="Study", methods=["Interview"], deliverables=["Report"])
    with pytest.raises(ValidationError, match="duplicate workstream"):
        ConsultingApproach(
            based_on_requirement_version_id=uuid4(),
            rationale="Pilot",
            workstreams=[w, w],
        )
