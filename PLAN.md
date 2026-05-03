# Code-Swarm PR #25 Ultimate SOTA Best-Practices Plan

**Repo:** `OpenSIN-Code/Code-Swarm`  
**PR:** [#25 Launch CEO Transformation Playbook and enhance production stability](https://github.com/OpenSIN-Code/Code-Swarm/pull/25)  
**Branch:** `product-market-review` → `main`  
**Updated:** 2026-05-03  
**Mode:** Plan only. No issue closes until its acceptance gate is green.

---

## 0. Current PR Facts

| Item | State |
| --- | --- |
| PR state | Open |
| Mergeability | Mergeable / clean |
| Vercel preview | Ready |
| Changed files | 21 |
| Additions / deletions | +2567 / -804 |
| Main themes | API gateway, WebSockets, CLI UX, persistence, MkDocs docs, version correction |

### Open Issues Covered or Touched

| Issue | Theme | Current plan status |
| --- | --- | --- |
| #9 | API Gateway, gRPC, OpenAPI, rate limiting | Validate implementation before close |
| #10 | Kubernetes, HPA, Istio, multi-tenancy | Separate infra gate required |
| #11 | Real-time WebSockets and streaming | Validate auth, limits, backpressure |
| #12 | CLI UX with Rich, progress, autocomplete | Validate API-backed CLI workflows |
| #13 | MkDocs, Swagger, tutorials, architecture | Validate strict docs build |
| #14 | RLHF/self-improvement loops | P2 implementation plan required |
| #19 | Hybrid memory with Qdrant + Neo4j | P2 implementation plan required |

---

## 1. Non-Negotiable Stop Gates

### 1.1 Secret Hygiene Gate

Merge is blocked until all checks are green:

- [ ] No real secrets in repository files.
- [ ] `.env.example` contains placeholders only.
- [ ] `README.md`, `SECURITY.md`, docs, comments, and scripts contain no API keys, JWTs, passwords, service keys, or full DB URLs.
- [ ] All required runtime values exist only in Infisical and deployment environment variables.
- [ ] Any token/key previously exposed in chat, docs, commits, or examples is rotated.
- [ ] `gitleaks detect` is clean.
- [ ] `trufflehog git file://.` is clean.

### 1.2 Reality-Claim Gate

- [ ] README status table matches code and tests.
- [ ] No “GA”, “production-ready”, or “100% complete” claim without verified tests and deployment evidence.
- [ ] Version remains beta unless all P0/P1 acceptance gates are green.
- [ ] Docs label P2 work as planned, not implemented.

### 1.3 Merge Gate

- [ ] Unit tests pass.
- [ ] Auth/security tests pass.
- [ ] WebSocket tests pass.
- [ ] CLI smoke tests pass against a running API.
- [ ] `mkdocs build --strict` passes.
- [ ] Vercel preview smoke test passes.
- [ ] PR diff has no hardcoded IPs, hostnames, or secrets.
- [ ] Manual QA notes are posted on PR #25.

---

## 2. Required Environment Variables

Runtime configuration must be read from environment variables. Values must not be committed.

| Variable | Required for | Source of truth |
| --- | --- | --- |
| `DATABASE_URL` | API persistence | Infisical + deploy env |
| `REDIS_URL` | rate limit/cache/queues | Infisical + deploy env |
| `SUPABASE_URL` | Supabase client | Infisical + deploy env |
| `SUPABASE_ANON_KEY` | public Supabase client | Infisical + deploy env |
| `SUPABASE_SERVICE_KEY` | server-only Supabase access | Infisical + deploy env |
| `SIMONE_MCP_URL` | Simone-MCP bridge | Infisical + deploy env |
| `PRIMARY_MODEL` | default agent model | Infisical + deploy env |
| `VISION_MODEL` | vision/look_at model | Infisical + deploy env |
| `SECRET_KEY` | JWT/session signing | Infisical + deploy env |
| `ALLOWED_ORIGINS` | CORS | Infisical + deploy env |
| `ENVIRONMENT` | runtime safety mode | deploy env |
| `SENTRY_DSN` | error monitoring | Infisical + deploy env |

Expected model defaults:

- `PRIMARY_MODEL=fireworks-ai/minimax-m2.7`
- `VISION_MODEL=nvidia/nvidia/nemotron-3-nano-omni`

---

## 3. Issue Acceptance Matrix

### #9 API Gateway

Scope:

- FastAPI REST endpoints.
- gRPC integration.
- OpenAPI/Swagger visibility.
- Rate limiting on every sensitive endpoint.

Acceptance:

- [ ] `api/main.py` imports cleanly.
- [ ] App starts locally with required env vars.
- [ ] `/health` returns healthy.
- [ ] `/docs` exposes accurate OpenAPI.
- [ ] Rate limit test proves throttling.
- [ ] No hardcoded Simone URL/IP.

### #10 Kubernetes and Auto-Scaling

Scope:

- Helm chart.
- HPA.
- Istio or documented service mesh path.
- Multi-tenant configuration.

Acceptance:

- [ ] `helm lint` passes.
- [ ] `helm template` renders manifests.
- [ ] HPA references real metrics.
- [ ] Secrets are referenced via Kubernetes Secret or external secret provider, never inline.
- [ ] Deployment guide includes k3s/OCI path and rollback.

### #11 WebSockets

Scope:

- JWT-authenticated real-time agent/task streams.
- Per-user limits.
- Backpressure.
- Monitoring endpoint.

Acceptance:

- [ ] Connect without token is rejected.
- [ ] Connect with invalid token is rejected.
- [ ] Connect with valid token succeeds.
- [ ] Per-user connection limit works.
- [ ] Message rate limit works.
- [ ] Backpressure warning is observable.
- [ ] Disconnect cleanup removes connection state.

### #12 CLI UX

Scope:

- Rich tables.
- Progress spinners.
- Autocomplete support.
- API-backed commands.
- Human-readable errors.

Acceptance:

- [ ] `code-swarm --help` renders.
- [ ] `code-swarm login` stores token securely.
- [ ] `code-swarm agents` works against API.
- [ ] `code-swarm tasks` works against API.
- [ ] `code-swarm create-agent` validates inputs.
- [ ] `code-swarm create-task` validates priority.
- [ ] API unavailable path returns clear error.

### #13 Documentation

Scope:

- MkDocs.
- Swagger/OpenAPI reference.
- Architecture guide.
- CLI guide.
- Vercel deployment guide.

Acceptance:

- [ ] `mkdocs build --strict` passes.
- [ ] Docs do not expose secrets.
- [ ] Architecture diagrams match code.
- [ ] API docs match OpenAPI output.
- [ ] Deployment guide uses environment variables only.
- [ ] README links point to real files.

### #14 RLHF / Self-Improvement

Scope:

- Feedback capture.
- Error analysis.
- Bayesian optimization loop.

Acceptance for planning phase:

- [ ] Design document exists.
- [ ] Data model for feedback is specified.
- [ ] Privacy/security constraints are specified.
- [ ] Implementation tickets are created.

Acceptance for implementation phase:

- [ ] Feedback events persist.
- [ ] Scoring pipeline has tests.
- [ ] Opt-out/deletion path exists.

### #19 Hybrid Memory

Scope:

- Qdrant vector memory.
- Neo4j graph memory.
- Adapter interface.
- Retrieval policy.

Acceptance for planning phase:

- [ ] Architecture document exists.
- [ ] Adapter contracts are specified.
- [ ] Data retention and deletion are specified.
- [ ] Implementation tickets are created.

Acceptance for implementation phase:

- [ ] Qdrant adapter tests pass.
- [ ] Neo4j adapter tests pass.
- [ ] Hybrid retrieval tests pass.
- [ ] Failure fallback is documented and tested.

---

## 4. Verification Commands

Run from repository root after checking out PR #25 branch.

```bash
python -m pip install -r requirements.txt
python -m pytest tests/unit -q
python -m pytest tests/unit/test_security.py -q
python -m pytest tests/unit/test_core.py -q
python -m compileall api auth cli db simone_mcp streaming swarm_pipeline
mkdocs build --strict -f docs/mkdocs.yml
gitleaks detect --source . --no-git
trufflehog filesystem . --no-update
```

Runtime smoke:

```bash
ENVIRONMENT=development \
SECRET_KEY=dev-only-local-secret \
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173 \
SIMONE_MCP_URL=http://localhost:8234 \
PRIMARY_MODEL=fireworks-ai/minimax-m2.7 \
VISION_MODEL=nvidia/nvidia/nemotron-3-nano-omni \
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Then verify:

```bash
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/docs
python -m cli.main health
```

---

## 5. Deployment Plan

### 5.1 Vercel

- [ ] Link Vercel project to `OpenSIN-Code/Code-Swarm`.
- [ ] Configure env vars via Vercel dashboard/API, sourced from Infisical.
- [ ] Deploy preview from PR #25.
- [ ] Run browser/API smoke on preview.
- [ ] Promote to production only after gates pass.

### 5.2 Monitoring

- [ ] Prometheus metrics endpoint documented and tested.
- [ ] Grafana dashboard JSON added or linked.
- [ ] Sentry DSN configured in deploy env.
- [ ] Alerts configured for error rate, latency, auth failure spikes, and websocket connection pressure.
- [ ] Runbook documents owner, severity, and rollback.

### 5.3 Rollback

- [ ] Vercel previous deployment rollback documented.
- [ ] Database migration rollback documented.
- [ ] Feature flags or env toggles documented for WebSockets and persistence.

---

## 6. PR #25 Review Checklist

- [ ] Check out `product-market-review`.
- [ ] Rebase/merge latest `main` if required.
- [ ] Run all verification commands.
- [ ] Review changed files for env-only config.
- [ ] Review docs for truthfulness and secret leaks.
- [ ] Validate Vercel preview.
- [ ] Post verification evidence to PR #25.
- [ ] Merge PR #25 only after all gates pass.
- [ ] Close issues only after their acceptance criteria are verified.

---

## 7. Immediate Next Work Items

1. Rotate exposed tokens/secrets and purge them from examples.
2. Replace `.env.example` values with placeholders.
3. Run secret scans and fix findings.
4. Run tests and docs strict build on PR #25.
5. Add missing tests for WebSockets, rate limits, and CLI API flows.
6. Convert #14 and #19 into concrete implementation tickets.
7. Complete Vercel env setup from Infisical and run preview smoke.

---

## 8. Stop Condition

This plan is complete when the file is committed or intentionally left as a working-tree plan update. Execution must stop after creating/updating this plan unless explicitly asked to continue.
