"""No network required: evidence traceability and permission boundaries."""
from uuid import uuid4
import pytest
from requirement_alignment.knowledge import (
    KnowledgeDocument, KnowledgeKind, EvidenceVisibility,
    chunk_document, retrieve_knowledge,
)


def doc(tenant, user, project=None, text="小红书年轻消费者研究、护肤品牌内容策略", **kwargs):
    return KnowledgeDocument(
        tenant_id=tenant, allowed_actor_ids={user}, project_id=project,
        title="Synthetic methodology", kind=KnowledgeKind.METHODOLOGY,
        source_name="SYNTHETIC-DEMO.txt", content=text, **kwargs
    )


def test_cjk_search_and_verbatim_source_offsets():
    tenant, user = uuid4(), uuid4()
    d = doc(tenant, user)
    hits = retrieve_knowledge("小红书 护肤", [d], tenant_id=tenant, actor_id=user)
    assert hits and hits[0].excerpt == d.content[hits[0].start:hits[0].end]


def test_no_cross_tenant_or_cross_user_or_project_leaks():
    tenant, user, project = uuid4(), uuid4(), uuid4()
    d = doc(tenant, user, project)
    assert not retrieve_knowledge("护肤", [d], tenant_id=uuid4(), actor_id=user, accessible_project_ids={project})
    assert not retrieve_knowledge("护肤", [d], tenant_id=tenant, actor_id=uuid4(), accessible_project_ids={project})
    assert not retrieve_knowledge("护肤", [d], tenant_id=tenant, actor_id=user)
    assert retrieve_knowledge("护肤", [d], tenant_id=tenant, actor_id=user, accessible_project_ids={project})


def test_no_results_means_empty_not_fabricated_case():
    tenant, user = uuid4(), uuid4()
    assert retrieve_knowledge("护肤", [], tenant_id=tenant, actor_id=user) == []
    assert retrieve_knowledge("unrelated", [doc(tenant,user)], tenant_id=tenant, actor_id=user) == []


def test_document_chunking_offsets_and_overlap():
    d = doc(uuid4(), uuid4(), text="a" * 2100)
    chunks = chunk_document(d, chunk_size=900, overlap=100)
    assert len(chunks) == 3
    assert all(c.text == d.content[c.start:c.end] for c in chunks)
    assert chunks[0].end - chunks[1].start == 100


def test_confidentiality_defaults_to_internal():
    d = doc(uuid4(),uuid4())
    assert d.visibility is EvidenceVisibility.INTERNAL_ONLY


def test_invalid_chunk_settings_rejected():
    with pytest.raises(ValueError):
        chunk_document(doc(uuid4(),uuid4()),chunk_size=100,overlap=100)
