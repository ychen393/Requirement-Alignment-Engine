# Requirement Alignment Engine — Consulting Proposal MVP PRD
Status: Draft V0.1 | Date: 2026-10-13 | Branch: feat/consulting-proposal-mvp

## 1. Product decision
Reposition the existing Requirement Alignment Engine as a **consultant-led client brief alignment and proposal drafting workspace** for small consulting and marketing agencies. Preserve the original engine and migrate incrementally. Do **not** build a general-purpose project management tool.

### Job to be done
When an account manager / consultant receives an incomplete client brief, they need to establish the client's intended business problem, agree on what will and will not be delivered, select a defensible approach, and produce an editable, client-reviewable proposal without fabricating facts.

### Primary persona
Agency account lead / consultant / engagement PM who receives client requests and owns the first proposal. Secondary persona: reviewer / consulting lead. Client is a recipient/reviewer, **not** a required authenticated user in MVP.

### Explicit non-goals
No workforce allocation, org charts, approvals engine, automated project staffing, task execution tracking, client-facing editing portal, or integrations with Jira/Feishu. No fabricated quantitative benchmarks, historical client outcomes, citations, budgets, or commitment dates. No automatic client delivery or final approval.

## 2. Value hypothesis (not validated)
Compared with an unstructured chat assistant, the workspace may reduce missed clarifications, unsupported proposal claims, and effort to produce a consistent first proposal. These are assumptions to test, not proven benefits.

## 3. Canonical user journey
1. **New project**: consultant types/pastes a brief and optional context (industry, target market, intended proposal type); save source verbatim.
2. **Analysis**: AI extracts explicitly stated facts, ambiguities, conflicting details, assumptions, material unknowns and candidate objectives, each with provenance.
3. **Clarification**: consultant answers priority questions, marks unknowns unresolved or not applicable, edits interpretation; regenerate normalized requirement draft from the answers.
4. **Approval gate**: consultant reviews objective, scope, out-of-scope, constraints, deliverables and acceptance conditions; persist an immutable confirmed requirement version.
5. **Approach design**: AI proposes appropriate workstreams/methods, data required, limitations and rationale. Case retrieval is **optional**: if no indexed, authorized cases exist, state that fact and continue without matches.
6. **Proposal drafting**: generate a structured proposal from the confirmed version, approach and approved evidence. Unresolved items must be shown as assumptions/open decisions, not facts.
7. **Review**: consultant edits sections and marks blocking issues resolved; reviewer checks claims, data provenance, feasibility and external language. No automatic publication.
8. **HTML delivery**: generate a branded but restrained client-ready HTML presentation / web document, preview, and export. Preserve proposal version and traceability. Editable PPTX export is a later milestone.

### Revisions
Any subsequent brief change creates a new requirement revision and proposed impact on approach/proposal sections; prior approvals remain immutable and are not silently reused for changed content.

## 4. MVP scope and priority
P0: text brief entry; analysis and targeted clarifications; answer/review workflow; confirmed requirement snapshot; consulting approach; structured proposal drafting; claim/evidence review; editable sections; HTML preview/export; project and version persistence; explicit AI/DEMO labeling; failures/retry.
P1: case library upload/indexing with permissions and grounded retrieval, branded themes, proposal diff, reviewer workflow.
P2: PPTX renderer, multi-tenant collaboration, CRM/Feishu/Jira integrations, advanced analytics.

### Important MVP tradeoff
A simple, explicitly curated mini-case library can be used for testing. Never claim an AI-generated demonstration case is a real historical engagement. For the first functional slice, retrieval can return 'no cases available' gracefully.

## 5. Screens / UI states (UI after contracts)
- Workspace: projects, statuses, latest saved proposal versions
- Intake: brief input, source metadata, import status
- Analysis: known / inferred / unresolved / contradicted with linked source excerpts
- Alignment: clarification answers, edited requirement, approval control
- Approach: methods, workstreams, dependencies and case evidence
- Proposal studio: structured section editor, validation issues, HTML preview, export/version history
Every async screen needs loading, partial-success, error, retry and empty states.

## 6. Acceptance tests
A. Given 'Improve our brand impact with Gen Z on Xiaohongshu' without budget or metric, output must NOT invent budget, promised lift, age bracket, region, dates, or verified performance.
B. User answers a clarification; the newly generated requirement and subsequent proposal must incorporate that exact answer, not a draft generated before the answer.
C. User edits and confirms requirement V1; readback from a new browser session yields the same immutable V1; a later edit creates V2, not overwrite V1.
D. For every client-facing factual claim, show source evidence, confirmed stakeholder input, or an explicit assumption. Unsupported claims block clean 'ready for client review' status.
E. Given zero available case documents, UI states 'No authorized historical cases found' and still supports proposal generation.
F. Given an LLM timeout / schema-invalid reply, preserve confirmed data and report actionable retry; no misleading successful artifact.
G. HTML export contains approved sections, no hidden internal notes or secrets, and faithfully matches the proposal version.
H. DEMO mode clearly identifies fixtures; AI mode cannot silently fall back to fixtures.

## 7. Security and deployment constraints
Repository is public: never commit client briefs, access tokens, or DB secrets. Default to synthetic/de-identified test documents. Authenticated server-side confirmation, scoped data access and audit trail are prerequisites for real client projects. Encryption, retention/deletion, backups and access policies require review before production. Database choice (e.g. managed PostgreSQL) is proposed, not yet implemented.

## 8. Success metrics for pilot
With 3–5 agency/consulting users and de-identified briefs: proportion of material gaps surfaced, critical hallucination count, proportion of sections requiring major rewrite, completion time relative to user's existing workflow, willingness to reuse. Record raw observations; do not pre-claim speed improvements.

## 9. Existing repository integration
Reuse Python FastAPI, Pydantic models, AI provider abstraction, requirement analyzer, clarification contracts, versioning logic and automated tests. Adapt execution planning into consulting approach; demote completion evaluation to optional proposal QA. Correct current frontend hardcoded Benchmark metadata, session-only data, and premature proposal generation. See docs/migration-plan.md.
