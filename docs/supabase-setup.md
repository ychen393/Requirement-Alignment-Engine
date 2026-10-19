# Supabase implementation — Sprint 4.2 foundation

Status: **migration and configuration contract only**. No Supabase project has been provisioned or connected, and no real client documents have been uploaded.

## Why Supabase
Managed Postgres + pgvector + private object storage + Auth. Keep FastAPI responsible for application authorization and controlled ingestion; browser clients must never receive a service_role key.

## Dev provisioning checklist
1. Create a dedicated Supabase development project under your organization's ownership. Record the project URL privately.
2. Review and apply `supabase/migrations/202610190001_knowledge_foundation.sql` using versioned migrations (not copy/paste in production).
3. Create a **private**, nonpublic storage bucket `enterprise-knowledge-private`; add explicit scoped access policies before client uploads. No bucket/public upload is automatically provisioned by this change.
4. Configure only backend Vercel Preview environment variables `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_KNOWLEDGE_BUCKET`. Never use `NEXT_PUBLIC_` for the service role.
5. Auth is a prerequisite for document ingest. Verify JWT identity and server-side organization membership, project scope and document grants. The existing demo frontend does **not** meet these requirements.
6. Validate cross-tenant and cross-user isolation with separate auth users and test RLS through an actual Supabase integration suite. Unit tests are not a substitute.
7. Validate upload limits, MIME type/content checks, private signed access, checksum/de-duplication, revoked document deletion, backup/restore and audit logging before any real customer data.

## Data model
kb_organizations, kb_memberships, kb_projects, kb_documents, kb_document_access, kb_chunks. `kb_chunks.embedding` uses vector(1536) as an **initial example only**: verify the chosen embedding model dimensions before indexing. Original files belong in private Supabase Storage; database stores paths, metadata and extracted chunks.

## Security decisions
Tables have RLS enabled and only restrictive authenticated read policies; no browser write policies. Writes must be enforced through an authenticated API that checks actor and tenant. Backend service-role privileges bypass RLS: validate authorization *before* any service-role operation.

## Known limitations and planned follow-up
- No file processing/embedding/pgvector index/retrieval RPC implemented yet.
- No authentication or private storage provisioning yet.
- No application integration with the existing in-memory lexical retriever yet.
- No schema migrations executed against a real database.
- Do not classify this as a complete RAG pipeline.
