# Vercel multi-service deployment notes

This branch contains a draft multi-service configuration. Review service names and public routes before production rollout.

## Public route allocation
- Next.js service `frontend` handles `/`, `/new`, `/alignment`, `/execution`, `/review`, and other ordinary UI paths.
- FastAPI service `app` handles `/requirements/*`, `/plans/*`, `/changes/*`, `/completion/*`, `/consulting/*`, and `/health`.
- There is deliberately **no** `/api` prefix rewrite: current FastAPI endpoints already use the above paths.
- Requests preserve their original paths; no path transform is required.

## Why no service binding yet?
The current frontend calls FastAPI from client-side React via `fetch`, not from a Next.js server function. Browser traffic uses public same-origin paths and the top-level rewrites. Private service bindings only work from server runtime, not browser or build. The reviewed code has no internal service-to-service calls, so no `bindings` entries are required. When server-side calls are introduced, add a binding on `frontend` to `app` (e.g. `BACKEND_INTERNAL_URL`) and change those server-only callers.

## Environment
- Set `APP_MODE=DEMO` on a preview deployment to avoid accidental real model invocation.
- For `AI` mode set `APP_MODE=AI`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY`, and optionally `LLM_TIMEOUT_SECONDS` **only on the backend**. Never commit secrets.
- Production browser client defaults to same-origin API paths. Do not set `NEXT_PUBLIC_API_BASE_URL` to localhost. If it is already set on Vercel, remove it unless intentionally overriding.
- The backend uses a src-layout Python package, so verify that Vercel's Python build installs `pyproject.toml` and imports `requirement_alignment.api.main:app`. Detection in the UI is not evidence of successful runtime import.
- Current FastAPI CORS defaults to localhost:3100. Same-origin Vercel browser calls do not require cross-origin CORS; do not use a wildcard with credentials.
- All services should be tested on a feature-branch preview first. Vercel's import view currently showed `main`; these files are not on main until merged.

## Validation
1. Test locally: install Python package, run backend at port 8100, frontend at 3100; perform app's existing workflow.
2. In a preview deployment: GET `/health` should return the backend mode; GET `/` should return the Next.js workbench.
3. Confirm `/new`, `/alignment` and `/_next/static/*` are routed to Next.js.
4. POST `/requirements/analyze` and POST `/consulting/approach` with appropriate typed payloads; confirm no API 404/path-prefix mismatch.
5. Test HTML preview with synthetic data and inspect generated page.
6. Ensure real customer data are NOT uploaded: authentication and persisted server-side review are not yet implemented.

## Before rollout — user approval needed
Confirm service names (`app`, `frontend`), public backend path groups, public Next.js catch-all, and no private bindings under current client-side fetch design. Do not merge this branch without that confirmation.
