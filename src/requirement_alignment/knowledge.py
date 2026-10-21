"""Knowledge ingestion and retrieval prototype; no database or embedding service.

This is a pure, deterministic, authorization-aware retrieval core for synthetic
text fixtures. The caller must authenticate and derive tenant/actor permissions.
Never instantiate it as a production enterprise knowledge store.
"""
from enum import Enum
from hashlib import sha256
import re
from uuid import UUID, uuid4
from pydantic import Field, model_validator
from requirement_alignment.consulting import StrictModel


class KnowledgeKind(str, Enum):
    CASE = "CASE"
    METHODOLOGY = "METHODOLOGY"
    RESEARCH = "RESEARCH"
    TEMPLATE = "TEMPLATE"


class EvidenceVisibility(str, Enum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    CLIENT_SHAREABLE = "CLIENT_SHAREABLE"


class KnowledgeDocument(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    project_id: UUID | None = None
    title: str = Field(min_length=1)
    kind: KnowledgeKind
    source_name: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=200_000)
    visibility: EvidenceVisibility = EvidenceVisibility.INTERNAL_ONLY
    allowed_actor_ids: set[UUID] = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    checksum: str = ""

    @model_validator(mode="after")
    def with_checksum(self):
        if not self.checksum:
            self.checksum = sha256(self.content.encode()).hexdigest()
        return self


class KnowledgeChunk(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    sequence: int = Field(ge=0)
    text: str = Field(min_length=1)
    # Character offsets preserve evidence positions for original source text.
    start: int = Field(ge=0)
    end: int = Field(gt=0)


class KnowledgeHit(StrictModel):
    document_id: UUID
    chunk_id: UUID
    title: str
    kind: KnowledgeKind
    excerpt: str
    source_name: str
    start: int
    end: int
    score: int = Field(ge=1)
    visibility: EvidenceVisibility


def chunk_document(document: KnowledgeDocument, chunk_size: int = 900, overlap: int = 100) -> list[KnowledgeChunk]:
    if not (100 <= chunk_size <= 5000 and 0 <= overlap < chunk_size):
        raise ValueError("invalid chunk size/overlap")
    text = document.content
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(KnowledgeChunk(document_id=document.id, sequence=len(chunks),
                                     text=text[start:end], start=start, end=end))
        if end == len(text):
            break
        start = end - overlap
    return chunks


def _tokens(text: str) -> set[str]:
    # Initial multilingual lexical scorer: Unicode words plus CJK bigrams.
    words = set(re.findall(r"[a-z0-9]+", text.casefold()))
    cjk = re.findall(r"[\u3400-\u9fff]+", text)
    for phrase in cjk:
        if len(phrase) == 1:
            words.add(phrase)
        else:
            words.update(phrase[i:i + 2] for i in range(len(phrase) - 1))
    return words


def retrieve_knowledge(
    query: str, documents: list[KnowledgeDocument], *, tenant_id: UUID,
    actor_id: UUID, accessible_project_ids: set[UUID] | None = None,
    top_k: int = 5,
) -> list[KnowledgeHit]:
    if not query.strip() or not 1 <= top_k <= 30:
        raise ValueError("query and top_k are required")
    projects = accessible_project_ids or set()
    q = _tokens(query)
    results: list[KnowledgeHit] = []
    for doc in documents:
        # Security filters before scoring AND before returning evidence.
        if (doc.tenant_id != tenant_id or actor_id not in doc.allowed_actor_ids
                or (doc.project_id is not None and doc.project_id not in projects)):
            continue
        for part in chunk_document(doc):
            score = len(q & _tokens(part.text))
            if score:
                results.append(KnowledgeHit(
                    document_id=doc.id, chunk_id=part.id, title=doc.title,
                    kind=doc.kind, excerpt=part.text, source_name=doc.source_name,
                    start=part.start, end=part.end, score=score,
                    visibility=doc.visibility,
                ))
    return sorted(results, key=lambda h: (-h.score, str(h.document_id), h.start))[:top_k]
