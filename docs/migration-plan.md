# Incremental Migration & Build Gates
Status: Draft V0.1, no code or infrastructure changes made.

## Current verified repository observations (static review)
- Existing Next.js frontend in frontend/; FastAPI/Pydantic services under src/requirement_alignment/.
- AI and DEMO modes deliberately separated; DEMO uses hard-coded model-benchmarking data.
- Browser sessionStorage keeps workspace state; API describes itself as stateless; no database/auth.
- Requirement analysis, questions, versioning, execution plan, change analysis, and completion evaluation have contracts.
- Notable flow issue: frontend alignment page can request a requirement proposal before clarification questions are answered; subsequent answers are not reliably fed into the proposal.
- frontend/lib/api.ts uses hardcoded Benchmark title, submitted_by, and source; local confirmation helper only changes a JSON status.
- Existing tests exist; their pass/fail status was **not** established by static review. No live model quality or deployed availability was verified.

## Phase 0 — baseline safety gate
1. Branch feat/consulting-proposal-mvp off main; leave main untouched.
2. Run pytest, frontend build, TypeScript verification, and lint command check; record actual results and fix regressions separately.
3. Add representative synthetic skincare agency brief and adversarial briefs as fixtures.
4. Identify all hardcoded demo text and prevent unmarked fixture output on real paths.

## Phase 1 — contract-first functional slice
1. Add consulting Pydantic models, validation, TypeScript parity and tests.
2. Fix clarification sequencing: analyze -> answer/explicitly defer -> draft -> review -> server-confirm.
3. Add consulting approach and proposal structured generation; source/evidence and claim checks.
4. Implement static, deterministic HTML renderer of ProposalDocument; editable UI preview.
5. Preserve legacy workflows until new flow passes contract, end-to-end and user acceptance tests.

## Phase 2 — persistence
1. Adopt managed Postgres only after schema review; migrations checked into repository.
2. User/project authorization, server audit log, immutable requirement and proposal versions.
3. Data retention, backup/export/restore and secret-management QA before real client briefs.
4. Curated retrieval pilot with source attribution, access filtering and no-match state.

## Phase 3 — presentational outputs
Brand themes, higher-fidelity HTML, PPTX with the same ProposalDocument contract; avoid generating separate inconsistent proposal narratives.

## Architectural decisions to test, not assume
- Existing OpenAI-compatible provider remains default candidate. Compare optional Coze workflow integration on same test cases before migrating orchestration.
- Keep Python FastAPI as domain backend unless deployment evidence shows a concrete blocker.
- Repository must stay free of actual client confidential data; use synthetic/de-identified examples.
- Never mix Requirement Alignment Engine code with AgentLab.

## Release gates
- No fabricated evidence/metrics or fake cases in client-facing exports.
- No unconfirmed requirement can be presented as stakeholder-approved.
- Resume after refresh; version stability across sessions once persistence added.
- Failures and retries never overwrite confirmed state.
- Production deployment only with authorization, database policies, backups and tested restoration.
