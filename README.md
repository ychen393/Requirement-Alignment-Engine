# Requirement Alignment Engine

A small domain foundation for turning vague requests into versioned, testable requirements and execution plans.

The MVP contains Pydantic domain contracts, a human-confirmed application workflow,
an optional OpenAI-compatible structured-output provider, a stateless FastAPI layer,
a document-centric Next.js web application, and a deterministic fallback demonstration.
It intentionally contains no database, authentication, or autonomous workflow engine.

## Development

Requires Python 3.11+.

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Run the deterministic, human-readable benchmark workflow without an API key:

```bash
python demo.py
```

Run the Phase 4 analysis smoke test explicitly in deterministic mode:

```bash
python smoke.py --mode DEMO
```

## API modes

The API never silently switches modes. Set `APP_MODE` to either `DEMO` or `AI`.

PowerShell example for the deterministic API:

```powershell
$env:APP_MODE = "DEMO"
uvicorn requirement_alignment.api.main:app --reload
```

AI mode requires an OpenAI-compatible chat-completions endpoint with JSON Schema
structured-output support:

```powershell
$env:APP_MODE = "AI"
$env:LLM_BASE_URL = "https://api.openai.com/v1"
$env:LLM_API_KEY = "..."
$env:LLM_MODEL = "..."
$env:LLM_TIMEOUT_SECONDS = "30"
uvicorn requirement_alignment.api.main:app --reload
```

See `.env.example` for the complete configuration. The application does not load
that file automatically; export the values through the shell or deployment platform.

Available endpoints:

- `POST /requirements/analyze`
- `POST /requirements/align`
- `POST /plans/generate`
- `POST /changes/analyze`
- `POST /completion/evaluate`
- `GET /health`

All generated artifacts are returned with `confirmation_status=AI_SUGGESTED`.
Endpoints that consume a confirmed requirement or execution plan reject an
`AI_SUGGESTED` input; the caller must explicitly resubmit it as `USER_CONFIRMED`.

## Human-in-the-loop boundaries

This product supports alignment; it does not autonomously manage a project.

AI may suggest missing information, clarification questions, scope, tasks,
acceptance criteria, diff explanations, and change-impact analysis. Those outputs
remain proposals until a person reviews them.

Users confirm requirement versions, execution plans, requirement changes, and
acceptance criteria. A user also makes the final completion decision whenever the
available evidence is missing, conflicting, or ambiguous.

## Frontend

The document-centric Next.js interface lives in `frontend/` and provides five routes:

- `/` — 工作台
- `/new` — 新建需求 / AI 分析
- `/alignment` — 需求对齐
- `/execution` — 执行计划 / 需求变更
- `/review` — 任务验收

Start the backend in DEMO mode:

```powershell
python -m pip install -e ".[dev]"
$env:APP_MODE = "DEMO"
$env:FRONTEND_ORIGIN = "http://localhost:3100"
uvicorn requirement_alignment.api.main:app --reload --port 8100
```

In another terminal, start the frontend:

```powershell
cd frontend
Copy-Item .env.local.example .env.local
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:3100`. This is the dedicated Requirement Alignment Engine web
application; port 3000 remains available to AgentLab. The frontend displays the active API mode and keeps
proposal/confirmation state in the browser session; there is intentionally no database.
