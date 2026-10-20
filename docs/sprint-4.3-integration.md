# Sprint 4.3 — Supabase integration status

Implemented:
- Development database contains six RLS-enabled knowledge tables, pgvector and private storage bucket.
- A Python REST adapter reads with the authenticated caller's bearer token rather than bypassing RLS with a privileged key.
- Unit tests exercise request headers and fail-closed input validation.

Not yet implemented:
- Frontend Supabase login and JWT lifecycle.
- Authenticated API endpoints and end-to-end permission tests with independent users.
- Document uploads, PDF/PPTX extraction, embeddings and hybrid retrieval.
- Production data access or Vercel credentials.

Next gates:
1. Confirm actual user authentication and session verification.
2. Test RLS using distinct users and organizations; verify unauthorized reads return no data.
3. Add private document ingestion with strict MIME, size, tenant and ACL checks.
4. Wire retrieved, attributable knowledge into Consulting Approach and Proposal Studio.

Do not accept browser-provided user IDs as authorization. Do not expose privileged Supabase keys to browser clients.
