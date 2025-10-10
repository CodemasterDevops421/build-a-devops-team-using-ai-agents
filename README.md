# DevOps AI Control Center

Production-ready platform combining FastAPI agents with a modern React control panel to automate CI/CD generation, Docker hardening, build prediction, and release monitoring.

## Features
- GitHub Actions workflow synthesis with deterministic lint/test stages
- Dockerfile authoring with secure base images and non-root guidance
- Build failure risk scoring using repository context signals
- Container image readiness checks resilient to offline Docker hosts
- Front-end dashboard with smooth animations, copy-to-clipboard actions, and structured toasts

## Architecture
- **Backend**: FastAPI + Pydantic with pluggable Supabase persistence, structured JSON logging, Prometheus metrics, and strict CORS controls (`ALLOWED_ORIGINS`)
- **Frontend**: React 18 + Vite + React Query + TypeScript, tested via Vitest/RTL
- **Testing**: `pytest` for Python agents/routes, Vitest for UI flows
- **Tooling**: Makefile targets, Dockerfiles for API/UI, Docker Compose for local orchestration
- **Observability**: `/healthz`, `/readyz`, `/metrics` (Prometheus), request IDs on every response, structured JSON logs

## Requirements
- Python 3.12+
- Node.js 20+
- npm 10+
- Optional: Docker 24+ for containerized workflows

## Environment Variables
| Variable | Purpose | Default |
| --- | --- | --- |
| `GROQ_API_ENDPOINT` | GROQ API base URL | `https://api.groq.com/v1` |
| `GROQ_API_KEY` | GROQ API token used by agents | _required_ |
| `SUPABASE_URL` | Optional Supabase REST endpoint | _in-memory fallback_ |
| `SUPABASE_KEY` | Optional Supabase service key | _in-memory fallback_ |
| `ALLOWED_ORIGINS` | Comma-separated list of CORS origins | `http://localhost:5173` |
| `REQUEST_ID_HEADER` | Header used to propagate request IDs | `X-Request-ID` |
| `METRICS_ENABLED` | Toggle Prometheus metrics endpoint | `true` |
| `VITE_API_BASE_URL` | Front-end API target | `http://localhost:8000` |

Duplicate `.env` files as needed from `frontend/.env.example` and `dot_env_example`.

## Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd frontend
npm install
```

### Run Services
```bash
# Backend
make backend-dev

# Frontend (new terminal)
make frontend-dev
```
The UI is served on `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

### Tests
```bash
# Python agents + API
make backend-test

# Front-end unit tests
make frontend-test

# Front-end lint + backend Ruff checks
make lint
```

## Docker & Compose
```bash
# Build standalone images
make docker-build

# Run full stack
make compose-up
# Tear down
make compose-down
```
The API image exposes port `8000`; the UI image serves static assets via NGINX on port `5173`.

## API Surface
- `POST /devops/generate-ci` → `{ pipeline_yaml, db_id }`
- `POST /devops/generate-dockerfile` → `{ dockerfile_content, db_id }`
- `POST /devops/predict-build` → `{ prediction, db_id }`
- `POST /devops/check-build-status` → `{ status, db_id }`
- `GET /healthz` / `GET /readyz` for monitoring probes

## Production Notes
- Configure secrets via environment variables or secret stores; the UI never persists API keys.
- Tune CORS by setting `ALLOWED_ORIGINS` to the deployed front-end hostname.
- Enable TLS termination at the ingress/load balancer; the containers expose HTTP by default.
- Add tracing by wiring OpenTelemetry instrumentation (hooks are in place via FastAPI middleware patterns).
- Front-end assets build to `dist/` and are served by NGINX with long-lived cache headers.
