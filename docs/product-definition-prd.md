# Product Definition (Brief + PRD)

## 1) Objective
Build a production-grade web application that trains new DevOps learners on the complete software delivery lifecycle while enabling practitioners to execute guided, controlled DevOps automation.

The product must ship a reliable MVP first, with safety and approval gates as core constraints.

## 2) Problem Statement
New engineers struggle to connect theory to real software delivery. Existing tutorials are either:
- Too shallow (slides-only, no execution context), or
- Too operationally risky (unbounded automation with weak guardrails).

Teams need one system that teaches **and** demonstrates practical workflow execution from intake to release operations.

## 3) Personas
- **Learner (Primary):** New DevOps or software engineer learning end-to-end lifecycle.
- **Practitioner (Primary):** DevOps engineer wanting assisted task orchestration with controls.
- **Reviewer/Approver (Secondary):** Senior engineer approving high-risk actions.
- **Admin (Secondary):** Maintains learning paths, modules, and governance settings.

## 4) Product Goals
- Deliver an MVP that provides lifecycle-aligned tutorials and controlled task orchestration.
- Support high reliability through deterministic workflows, idempotent operations, and auditable state.
- Ensure safety with explicit approval gates for risky actions.
- Keep training mode practical by exposing structured "decision rationale" tied to actual agent actions.

## 5) Non-Goals (MVP)
- No unrestricted direct production mutation.
- No fully autonomous cloud provisioning without mandatory human approval.
- No advanced visual simulation engine in MVP (deferred post-MVP).
- No broad multi-cloud IaC orchestration beyond curated, bounded scenarios.

## 6) Scope (MVP)

### In Scope
1. **Lifecycle Training Content**
   - Module-based tutorials mapped to SDLC/DevOps phases.
   - Step-by-step guidance with quiz checkpoints.
   - Structured decision logs explaining why specific actions are recommended.

2. **Controlled Orchestration**
   - Intake of project context and requirements.
   - Generated execution plan (task graph) with statuses.
   - Existing agents invoked via registry with contract validation.

3. **Approval Gates (Core Safety Feature)**
   - Rule-driven gate policy (e.g., deploy, infra change, secrets-sensitive actions).
   - Human approver workflow with approve/reject and reason capture.
   - Full audit trail per gate decision.

4. **Observability + Reliability**
   - /healthz, /readyz, metrics endpoint.
   - Structured logs with request correlation.
   - Retry/circuit-breaker strategy for external calls.

5. **Progress + Governance**
   - Learner progress tracking and completion.
   - Run history, artifacts, and approvals timeline.

### Deferred (Post-MVP)
- Rich visual lifecycle explorer with animations and interactive map.
- Sandbox ephemeral environments per learner.
- Advanced autonomous optimization loops.

## 7) Functional Requirements

### FR-1 Intake & Planning
- System accepts project goals, constraints, and optional repository context.
- System generates a task graph with explicit dependencies and estimated execution steps.
- User can edit/confirm plan before execution.

### FR-2 Agent Orchestration
- Orchestrator executes task nodes against registered agents.
- Agent responses validated against typed contracts.
- Task retries follow policy with bounded attempts and exponential backoff.

### FR-3 Training Mode (MVP form)
- Each orchestration step emits rationale log entries:
  - input considered,
  - decision made,
  - expected outcome,
  - fallback guidance.
- User can replay execution timeline for learning.

### FR-4 Approval Gate UX
- Risk-scored actions create `PENDING_APPROVAL` checkpoints.
- Approver receives in-app notification queue (MVP baseline).
- Approval form captures decision + reason + optional override notes.
- Rejection routes workflow to corrective branch with actionable feedback.

### FR-5 Auditability
- Immutable append-only event log for:
  - plan creation,
  - task start/end,
  - approvals,
  - failures/retries,
  - artifacts produced.

### FR-6 Learner Experience
- Tutorial module player with objectives, prerequisites, and checkpoints.
- Quiz attempts with score and explanation.
- Dashboard with completion and recommended next module.

## 8) Non-Functional Requirements
- API p95 latency target: <200ms for non-LLM standard endpoints.
- DB p95 latency target: <100ms for indexed reads in normal load.
- Test coverage target: >=80% for backend core domain and orchestration logic.
- Security baseline: authentication, RBAC, input validation, rate limiting, safe CORS defaults.
- Reliability SLO target for core API availability: 99.9% (excluding external LLM outages).

## 9) Approval Gate UX (MVP)
- **Trigger:** policy engine marks task as high-risk.
- **State transition:** `RUNNING -> PENDING_APPROVAL`.
- **Approver dashboard:** shows pending items, risk reason, diff/impact summary.
- **Actions:** approve, reject, request changes.
- **On approve:** resume from paused node.
- **On reject:** mark node failed with required remediation note.
- **Audit:** record actor, timestamp, decision payload.

## 10) Cost Model (Initial)
Assumptions for early MVP pilot:
- 100 monthly active learners.
- 20 orchestration runs/day average.
- Mixed LLM + deterministic execution.

Cost buckets:
- **LLM API:** primary variable cost; enforce token budgets and caching.
- **Compute:** API + worker pods (autoscaled baseline low).
- **Storage:** Postgres + object storage for artifacts/log exports.
- **Observability:** metrics/log retention.

Cost controls:
- Prompt/response truncation policies.
- Reuse deterministic templates before LLM calls.
- Cache repeated planning outputs for similar prompts.
- Hard per-workspace token quota and rate controls.

## 11) Delivery Plan (Adjusted)
Timeline assumes part-time execution with quality gates.

- **Phase A: Product Definition (1-2 weeks)**
  - Finalize this merged Brief + PRD.
  - Acceptance criteria and event taxonomy.

- **Phase B: Architecture + Contracts (2 weeks)**
  - Data model, agent registry contracts, failure matrix.
  - Integration design for existing agents.

- **Phase C: MVP Build (3-5 weeks)**
  - Intake, planning, orchestration, approval gates, training rationale logs.

- **Phase D: Hardening + Release (2-3 weeks)**
  - Security, test stabilization, performance, observability, release playbook.

**Total:** 8-12 weeks for MVP.

## 12) Acceptance Criteria (MVP)
- A learner can complete at least 5 lifecycle modules end-to-end.
- A practitioner can run a curated project workflow with at least one approval gate.
- Every orchestration run has complete audit trail and replayable rationale logs.
- Existing core agents are integrated via registry contracts and pass integration tests.
- CI enforces lint, tests, build, and security scan gates.

## 13) Open Decisions for Review
- Final set of risk rules for mandatory approvals.
- RBAC granularity for approver roles (team-level vs workspace-level).
- Artifact retention window and compliance requirements.
