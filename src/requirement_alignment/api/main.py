"""Minimal stateless API. All workflow state remains in request/response payloads."""

import os

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import ValidationError

from requirement_alignment.ai import (
    AIConfigurationError,
    AIProviderError,
    AIResponseError,
    AITimeoutError,
    ConfirmationStatus,
    LLMProvider,
    OpenAICompatibleProvider,
    Proposal,
    analyze_requirement_change_with_ai,
    analyze_requirement_with_ai,
    evaluate_completion_with_ai,
    generate_clarification_questions_with_ai,
    generate_execution_plan_with_ai,
    generate_requirement_proposal_with_ai,
)
from requirement_alignment.ai.change_analyzer import ChangeProposalBundle
from requirement_alignment.ai.approach_generator import generate_consulting_approach
from requirement_alignment.approach import ConsultingApproach
from requirement_alignment.consulting import ProposalDocument
from requirement_alignment.proposal_generator import generate_proposal
from requirement_alignment.html_renderer import render_proposal_html
from requirement_alignment.auth_verifier import AuthConfiguration, SupabaseAuthVerifier, AuthenticationError
from requirement_alignment.knowledge_repository import KnowledgeReaderConfig, SupabaseKnowledgeReader
from requirement_alignment.api.schemas import (
    AlignRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    AppMode,
    ChangeProposalResponse,
    ChangeRequest,
    CompletionProposalResponse,
    CompletionRequest,
    PlanProposalResponse,
    PlanRequest,
    RequirementProposalResponse,
    StatusResponse,
)
from requirement_alignment.models import RawRequirement, WorkflowState, RequirementVersion
from pydantic import BaseModel
from uuid import UUID


class ApproachRequest(BaseModel):
    requirement: Proposal[RequirementVersion]


class ApproachResponse(BaseModel):
    mode: AppMode
    proposal: Proposal[ConsultingApproach]


class ProposalGenerateRequest(BaseModel):
    project_id: UUID
    requirement: Proposal[RequirementVersion]
    approach: ConsultingApproach


class ProposalRenderRequest(BaseModel):
    proposal: ProposalDocument


class ConfirmationRequiredError(ValueError):
    pass


def _confirmed(proposal: Proposal, label: str):
    if proposal.confirmation_status is not ConfirmationStatus.USER_CONFIRMED:
        raise ConfirmationRequiredError(f"{label} must be explicitly USER_CONFIRMED")
    return proposal.payload


def _mode_from_env() -> AppMode:
    raw = os.getenv("APP_MODE", "").upper()
    if not raw:
        raise AIConfigurationError("APP_MODE must be explicitly set to AI or DEMO")
    try:
        return AppMode(raw)
    except ValueError as exc:
        raise AIConfigurationError("APP_MODE must be AI or DEMO") from exc


def create_app(
    *,
    mode: AppMode | None = None,
    provider: LLMProvider | None = None,
) -> FastAPI:
    app = FastAPI(title="Requirement Alignment Engine", version="0.4.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3100")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def runtime() -> tuple[AppMode, LLMProvider | None]:
        active_mode = mode or _mode_from_env()
        if active_mode is AppMode.AI:
            return active_mode, provider or OpenAICompatibleProvider.from_env()
        return active_mode, None

    @app.exception_handler(AIConfigurationError)
    async def configuration_error(_: Request, exc: AIConfigurationError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(AITimeoutError)
    async def timeout_error(_: Request, exc: AITimeoutError) -> JSONResponse:
        return JSONResponse(status_code=504, content={"detail": str(exc)})

    @app.exception_handler(AIResponseError)
    async def response_error(_: Request, exc: AIResponseError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(AIProviderError)
    async def provider_error(_: Request, exc: AIProviderError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(ConfirmationRequiredError)
    async def confirmation_error(_: Request, exc: ConfirmationRequiredError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def domain_validation_error(_: Request, __: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"detail": "The AI proposal did not satisfy domain validation"},
        )

    @app.exception_handler(ValueError)
    async def workflow_validation_error(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.get("/health", response_model=StatusResponse)
    def health() -> StatusResponse:
        try:
            active_mode, _ = runtime()
        except AIConfigurationError:
            return StatusResponse(mode=None, status="configuration_required")
        return StatusResponse(mode=active_mode, status="ok")

    @app.get("/knowledge/documents")
    def knowledge_documents(organization_id: UUID, authorization: str | None = Header(default=None)):
        """Authenticated scoped read; PostgreSQL RLS enforces membership + grants."""
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        if not url or not key:
            raise HTTPException(status_code=503, detail="Knowledge access is not configured")
        if not authorization:
            raise HTTPException(status_code=401, detail="Bearer token required")
        try:
            config = AuthConfiguration(url=url, publishable_key=key)
            SupabaseAuthVerifier(config).verify(authorization)
            token = authorization.split(" ", 1)[1].strip()
            return SupabaseKnowledgeReader(KnowledgeReaderConfig(
                url=url, publishable_key=key
            )).search_documents(token, str(organization_id))
        except AuthenticationError:
            raise HTTPException(status_code=401, detail="Authentication failed")
        except Exception as exc:
            # Avoid leaking upstream credentials, identity or raw DB errors.
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(status_code=502, detail="Knowledge read failed")

    @app.post("/requirements/analyze", response_model=AnalyzeResponse)
    def analyze(body: AnalyzeRequest) -> AnalyzeResponse:
        active_mode, active_provider = runtime()
        if active_mode is AppMode.DEMO:
            from requirement_alignment.demo_data import (
                ANALYSIS,
                CLARIFICATION_QUESTIONS,
                RAW_REQUIREMENT,
            )

            return AnalyzeResponse(
                mode=active_mode,
                raw_requirement=Proposal(
                    confirmation_status=ConfirmationStatus.USER_CONFIRMED,
                    payload=RAW_REQUIREMENT,
                ),
                analysis=Proposal(payload=ANALYSIS),
                clarification_questions=Proposal(payload=CLARIFICATION_QUESTIONS),
            )
        raw = RawRequirement(
            title=body.title,
            description=body.request,
            submitted_by=body.submitted_by,
            source=body.source,
            status=WorkflowState.NEEDS_CLARIFICATION,
        )
        analysis = analyze_requirement_with_ai(raw, active_provider)  # type: ignore[arg-type]
        questions = generate_clarification_questions_with_ai(
            raw, analysis.payload, active_provider  # type: ignore[arg-type]
        )
        return AnalyzeResponse(
            mode=active_mode,
            raw_requirement=Proposal(
                confirmation_status=ConfirmationStatus.USER_CONFIRMED, payload=raw
            ),
            analysis=analysis,
            clarification_questions=questions,
        )

    @app.post("/requirements/align", response_model=RequirementProposalResponse)
    def align(body: AlignRequest) -> RequirementProposalResponse:
        active_mode, active_provider = runtime()
        if active_mode is AppMode.DEMO:
            from requirement_alignment.demo_data import VERSION_V1

            proposal = Proposal(payload=VERSION_V1)
        else:
            proposal = generate_requirement_proposal_with_ai(
                body.raw_requirement,
                body.analysis,
                body.answered_clarification_questions,
                active_provider,  # type: ignore[arg-type]
            )
        return RequirementProposalResponse(mode=active_mode, proposal=proposal)

    @app.post("/plans/generate", response_model=PlanProposalResponse)
    def plan(body: PlanRequest) -> PlanProposalResponse:
        active_mode, active_provider = runtime()
        requirement = _confirmed(body.requirement, "RequirementVersion")
        if active_mode is AppMode.DEMO:
            from requirement_alignment.demo_data import EXECUTION_PLAN

            proposal = Proposal(payload=EXECUTION_PLAN)
        else:
            proposal = generate_execution_plan_with_ai(requirement, active_provider)  # type: ignore[arg-type]
        return PlanProposalResponse(mode=active_mode, proposal=proposal)

    @app.post("/consulting/approach", response_model=ApproachResponse)
    def consulting_approach(body: ApproachRequest) -> ApproachResponse:
        active_mode, active_provider = runtime()
        requirement = _confirmed(body.requirement, "RequirementVersion")
        if active_mode is AppMode.DEMO:
            from requirement_alignment.approach import Workstream
            proposal = Proposal(payload=ConsultingApproach(
                based_on_requirement_version_id=requirement.id,
                rationale="DEMO ONLY: illustrative consulting approach, not client advice.",
                workstreams=[Workstream(
                    title="Illustrative discovery",
                    objective="Clarify the confirmed requirement",
                    methods=["Stakeholder interviews"],
                    deliverables=["Discovery summary"],
                    data_required=["Client-approved inputs"],
                )],
                unknowns=["Demo content is synthetic"],
            ))
        else:
            proposal = generate_consulting_approach(requirement, active_provider)
        return ApproachResponse(mode=active_mode, proposal=proposal)

    @app.post("/consulting/proposal", response_model=ProposalDocument)
    def consulting_proposal(body: ProposalGenerateRequest) -> ProposalDocument:
        # This composer uses reviewed structured inputs; no fabricated research.
        requirement = _confirmed(body.requirement, "RequirementVersion")
        return generate_proposal(requirement, body.approach, project_id=body.project_id)

    @app.post("/consulting/proposal/preview", response_class=HTMLResponse)
    def consulting_proposal_preview(body: ProposalRenderRequest) -> HTMLResponse:
        return HTMLResponse(
            render_proposal_html(body.proposal, allow_draft_preview=True),
            headers={"Cache-Control": "no-store", "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"},
        )

    @app.post("/consulting/proposal/export", response_class=HTMLResponse)
    def consulting_proposal_export(body: ProposalRenderRequest) -> HTMLResponse:
        # Status is caller-supplied; this is NOT authenticated approval.
        # Keep the endpoint a draft-only artifact until persistent server review exists.
        return HTMLResponse(
            render_proposal_html(body.proposal, allow_draft_preview=True),
            headers={"Cache-Control": "no-store", "Content-Disposition": 'attachment; filename="proposal-DRAFT.html"', "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"},
        )

    @app.post("/changes/analyze", response_model=ChangeProposalResponse)
    def change(body: ChangeRequest) -> ChangeProposalResponse:
        active_mode, active_provider = runtime()
        requirement = _confirmed(body.current_requirement, "RequirementVersion")
        plan_value = _confirmed(body.current_plan, "ExecutionPlan")
        if active_mode is AppMode.DEMO:
            from requirement_alignment.demo_data import (
                DIFF,
                EXECUTION_PLAN_V2,
                IMPACT_ANALYSIS,
                VERSION_V2,
            )

            proposal = Proposal(
                payload=ChangeProposalBundle(
                    requirement_version=VERSION_V2,
                    requirement_diff=DIFF,
                    impact_analysis=IMPACT_ANALYSIS,
                    revised_execution_plan=EXECUTION_PLAN_V2,
                )
            )
        else:
            proposal = analyze_requirement_change_with_ai(
                body.raw_requirement,
                requirement,
                plan_value,
                body.stakeholder_change,
                active_provider,  # type: ignore[arg-type]
            )
        return ChangeProposalResponse(mode=active_mode, proposal=proposal)

    @app.post("/completion/evaluate", response_model=CompletionProposalResponse)
    def completion(body: CompletionRequest) -> CompletionProposalResponse:
        active_mode, active_provider = runtime()
        requirement = _confirmed(body.current_requirement, "RequirementVersion")
        plan_value = _confirmed(body.current_plan, "ExecutionPlan")
        if active_mode is AppMode.DEMO:
            from requirement_alignment.demo_data import COMPLETION_EVALUATION

            proposal = Proposal(payload=COMPLETION_EVALUATION)
        else:
            proposal = evaluate_completion_with_ai(
                requirement,
                plan_value,
                body.evidence_status,
                active_provider,  # type: ignore[arg-type]
            )
        return CompletionProposalResponse(mode=active_mode, proposal=proposal)

    return app


app = create_app()
