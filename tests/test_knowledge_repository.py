from uuid import uuid4
import pytest
from requirement_alignment.knowledge_repository import SupabaseKnowledgeReader, KnowledgeReaderConfig

def test_reader_uses_caller_authorization():
    observed = []
    def stub(url, headers):
        observed.append((url, headers))
        return []
    reader = SupabaseKnowledgeReader(
        KnowledgeReaderConfig(url="https://example.supabase.co", publishable_key="example-public-key"),
        transport=stub,
    )
    reader.search_documents("example-user-token", str(uuid4()))
    assert observed[0][1]["Authorization"] == "Bearer example-user-token"
    assert observed[0][1]["apikey"] == "example-public-key"
    assert "kb_documents" in observed[0][0]

def test_reader_rejects_missing_token():
    reader = SupabaseKnowledgeReader(
        KnowledgeReaderConfig(url="https://example.supabase.co", publishable_key="example-public-key")
    )
    with pytest.raises(ValueError):
        reader.search_documents("", str(uuid4()))

def test_reader_bounds_result_size():
    reader = SupabaseKnowledgeReader(
        KnowledgeReaderConfig(url="https://example.supabase.co", publishable_key="example-public-key")
    )
    with pytest.raises(ValueError):
        reader.search_documents("example-user-token", str(uuid4()), limit=1000)
