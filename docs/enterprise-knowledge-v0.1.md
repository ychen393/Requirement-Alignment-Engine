# Enterprise Knowledge Layer V0.1 — Contract & Implementation Decisions

## Scope and current status
This is a **non-persistent, synthetic-fixture, lexical retrieval prototype**. It is NOT a deployed enterprise RAG system, file upload service, vector DB, tenant authorization, or ingestion pipeline. Never connect confidential real clients to it. Code: `src/requirement_alignment/knowledge.py`.

## Four logical document classes
- CASE — historical project case, project background, method and outcome
- METHODOLOGY — approved frameworks and internal research processes
- RESEARCH — industry research and primary data with provenance and date
- TEMPLATE — proposal formats, presentation instructions and brand rules

## Canonical fields
KnowledgeDocument: id, tenant_id, project_id (optional), title, kind, source_name, content, version, checksum, allowed_actor_ids, visibility. Visibility defaults INTERNAL_ONLY. Chunk: document_id, sequence, start, end, text. Hit: document_id, chunk_id, source, exact excerpt, offsets, score and visibility.

## Ingestion contract for future production
1. Upload to private object storage (never a public static directory); require authenticated user and tenant.
2. Validate type (PDF/DOCX/PPTX/TXT), size, media and scanner; block macros/executables.
3. Parse with format-aware extractors, preserving page/slide/heading/table locators. Avoid OCR unless necessary.
4. Compute checksum, de-duplicate within tenant, store immutable source version and source metadata.
5. Chunk along document structure, preserving exact locators; index text and optional embeddings.
6. Index in Postgres (full-text + pgvector initially); run tenant/project/actor permission predicates *before* retrieval.
7. On document revocation/deletion, invalidate all chunks, embeddings, search cache and citations.
8. Record owner, provenance, retention schedule, last-reviewed date, client-sharing classification and access audit.
9. Evaluate extraction failure, relevance and access-leak tests before enabling upload.

## Retrieval strategy
V0.1 deterministic lexical scoring supports both ASCII terms and CJK bigrams; not semantic RAG. Production: metadata+ACL prefilter -> keyword/BM25 and vector candidate retrieval -> fusion/rerank -> cite exact source span -> human review and client-shareability filter. Do not show arbitrary similarity percentages without calibrated scoring.

## Trust policy
Historical documents are *untrusted content*, not instructions to execute. A relevant internal case is not proof that a method worked. No LLM-generated synthetic case can be labeled historical. Internal-only materials can inform consultant review but must not be copied verbatim into client deliverables without permission. Do not trust actor_id or tenant_id from unauthenticated browser requests.

## Persistence architecture (proposed, not installed)
Private object storage + managed PostgreSQL tables:
tenants, actors, memberships, projects, knowledge_documents, document_versions,
chunks, embeddings, document_acl, retrieval_events, citation_reviews.
Use migrations, tenant RLS/authorization, auth verification, backup/restore tests.
No open unauthenticated `/knowledge/upload` or `/knowledge/search` endpoint is created in V0.1.

## Evaluation gate
Start with 10–20 clearly synthetic/de-identified artifacts. Track relevant-hit recall@5, top-k citation accuracy, empty-corpus behavior, revocation correctness, forbidden cross-tenant hits (must be zero), and precision of proposed methodological reuse.

## Integration order
1. Approve metadata and access contract.
2. Add authenticated ingestion plus database migration and private storage.
3. Build hybrid retrieval with tracing, case relevance reasons and source spans.
4. Connect retrieval to Consulting Approach only as evidence suggestions.
5. Add verified client-safe citations to Proposal Studio.
