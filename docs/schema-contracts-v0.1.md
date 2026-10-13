# Consulting Proposal MVP — Input / Output Contracts V0.1
Status: Design draft; **not** a database migration or implemented API. Keep backend Pydantic as canonical contracts and generate/synchronize TypeScript types.

## 0. Cross-cutting policies
All persisted records: id (UUID), project_id, created_at, updated_at, schema_version; where applicable created_by. Never trust actor/approval identity supplied as a client-side label.

Provenance enum: CLIENT_EXPLICIT, CONSULTANT_CONFIRMED, SOURCE_DOCUMENT, AI_INFERRED, UNKNOWN.
Review status: DRAFT, NEEDS_CLARIFICATION, READY_FOR_REVIEW, CONFIRMED, CHANGES_REQUESTED.
Every asserted item may carry source_refs[] (source document id + bounded passage/locator), confidence as optional diagnostic (not evidence), reviewer_note and verification_status.
**Null means unknown**; never generate fake default budgets, KPIs, dates or case similarity percentages.

## 1. BriefIntake (input)
- project_name: string nonempty
- raw_brief: string nonempty, preserve verbatim
- source_type: MANUAL | EMAIL_PASTE | MEETING_NOTES | DOCUMENT
- industry: string | null
- client_name: string | null (may be pseudonym)
- geography: string | null
- engagement_type: string | null
- desired_output: PROPOSAL_HTML (MVP)
- attachments: SourceDocumentRef[] (MVP supports none or manually attached plain text only; file parsers separately specified)
Output: project_id, brief_id, submitted_at, processing_state.

## 2. RequirementAnalysis (LLM result, not automatically confirmed)
- confirmed_facts: EvidenceStatement[] {id, text, provenance, source_refs[]}
- proposed_objectives: EvidenceStatement[] (AI inferred until consultant confirms)
- uncertainties: Issue[] {id, target_field, question_or_issue, severity: BLOCKER|HIGH|LOW, rationale, source_refs[]}
- contradictions: Issue[]
- constraints: EvidenceStatement[]
- risks: Issue[]
- summary: string
Invariants: every CLIENT_EXPLICIT claim is traceable to the brief; AI hypotheses cannot be labeled confirmed; empty lists valid.

## 3. ClarificationQuestion / Answer
- question_id, target_field, question, rationale, priority, blocking: bool
- status: OPEN | ANSWERED | DECLINED | NOT_APPLICABLE
- answer: string | null
- answer_source: CLIENT | CONSULTANT_INTERPRETATION | DOCUMENT | null
- answered_by_actor_id: UUID | null (server derived)
- answered_at
Missing information may remain intentionally unresolved, **not** always forced into an answer. Blocking unresolved fields prevent CONFIRMED unless consultant explicitly accepts a named assumption with rationale.

## 4. ConfirmedRequirementVersion
- requirement_id, version_number, parent_version_id, raw_brief_id
- objective, business_context, target_audience (nullable), in_scope[], out_of_scope[], constraints[]
- intended_deliverables[], acceptance_criteria[] {criterion, evidence_required, validation_method}
- unresolved_assumptions[] {text, owner, decision_due | null}
- explicit_exclusions[], confirmed_by_actor_id, confirmed_at, confirmation_status
- immutable_snapshot_hash (derived on server)
Invariants: immutable once confirmed; updates always produce new revision; no client-side flag alone can establish approval.

## 5. CaseMatch (optional)
- case_id, title, industry, business_problem, approach_excerpt
- permission_scope, source_refs[], relevance_reasons[]
- score: number | null (only if a documented scoring method exists)
Do not invent cases or display artificial precision. If no accessible corpus, return [] + retrieval_status=EMPTY_CORPUS.

## 6. ConsultingApproach
- based_on_requirement_version_id
- rationale, workstreams[] {id, title, objective, methods[], activities[], deliverables[], dependencies[], evidence_needed[], assumptions[]}
- proposed_timeline: phases[] (duration may be null)
- feasibility_risks[], reused_case_refs[]
- status: AI_SUGGESTED | CONSULTANT_REVIEWED
Do not assert fixed dates/resources/budgets without source.

## 7. ProposalDocument (single source of truth for HTML and future PPTX)
- id, project_id, based_on_requirement_version_id, based_on_approach_id, version_number
- audience: CLIENT
- title, subtitle, executive_summary
- sections[] {id, type, heading, blocks[], claim_refs[], order}
- open_decisions[], limitations[], assumptions[], footnotes[], references[]
- brand_theme_key, status: DRAFT | REVIEW_REQUIRED | APPROVED_FOR_EXPORT
- quality_checks[] {check_id, severity: BLOCKER|WARNING, section_id | null, message, resolved_by | null}
- approved_by_actor_id | null, approved_at | null
Block types: PARAGRAPH, BULLETS, TABLE, PHASES, KEY_MESSAGE, QUOTE; charts in later versions only with backed data.
Proposed section types: CONTEXT, UNDERSTANDING, OBJECTIVES, APPROACH, WORKSTREAMS, DELIVERABLES, TIMELINE, ASSUMPTIONS, NEXT_STEPS.
Invariants: export renderer consumes ProposalDocument only, never calls LLM. Client-facing factual claims must be cited, confirmed or identified as assumptions. Preserve an export snapshot/hash.

## 8. Persistence entities (logical)
Project, Brief, SourceDocument, RequirementAnalysis, Clarification, RequirementVersion, CaseDocument, CaseMatch, ConsultingApproach, ProposalVersion, AuditEvent, ExportArtifact.
DB implementation needs foreign keys, version uniqueness by project, tenant scoping, immutable confirmations, least-privilege policies, transaction boundaries, migrations and tested restore. No employee roster or workforce capacity tables in MVP.

## 9. Proposed endpoint evolution (not implemented)
POST /projects; POST /projects/{id}/briefs; POST /briefs/{id}/analyze;
PUT /projects/{id}/clarifications/{question_id}; POST /projects/{id}/requirements/preview;
POST /projects/{id}/requirements/confirm; POST /projects/{id}/approaches/generate;
POST /projects/{id}/proposals/generate; PATCH /proposals/{id}; POST /proposals/{id}/review;
POST /proposals/{id}/export/html; GET /projects/{id}/history.
Use server authenticated actor identity, idempotency for mutating calls and optimistic version concurrency.
Keep legacy endpoints operational until tests certify their replacements.

## 10. Example behavior
Brief: 'Help our skincare brand reach younger customers through Xiaohongshu.'
Known: skincare category and platform; unknown: age definition, region, budget, baseline, expected KPI, schedule.
Valid result: prioritized client questions, provisional methods with disclosed assumptions; no invented '+30%' lift or '4-week guaranteed delivery'.
