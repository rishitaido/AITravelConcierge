# OpenQQuantify — AI Travel Platform

An AI-powered travel concierge that generates custom itineraries, offers conversational trip planning, and visualizes destinations on a 3D globe. Built with Flask, OpenRouter LLM APIs, and a full observability stack.

[![CI Pipeline](https://github.com/YOUR_USERNAME/airports.ai.OQQ/workflows/CI%20Pipeline/badge.svg)](https://github.com/YOUR_USERNAME/airports.ai.OQQ/actions)

---

## What It Does

- **AI Chat** — Ask TripMate anything about travel. It remembers your conversation and gives specific recommendations, not generic "what's your budget?" back-and-forth.
- **Itinerary Generator** — Pick a city, budget, pace, and travel style → get a day-by-day plan with morning/afternoon/evening activities and cost estimates.
- **3D Globe** — Browse destinations on an interactive MapLibre globe with an embedded AI chat for quick place lookups.
- **Caching** — Repeated prompts hit a local SQLite cache instead of the LLM, so responses are instant and API costs stay low.

---

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/airports.ai.OQQ.git
cd airports.ai.OQQ

# Copy .env.example or create .env with your keys
echo "OPENROUTER_API_KEY=your_key_here" > .env

# One command — sets up the venv, installs deps, starts the server
make dev
```

App runs at **http://localhost:8080**.

---

## Endpoints

| Route | What it does |
|-------|-------------|
| `/` | Home page with AI chat |
| `/itinerary` | Itinerary builder |
| `/globe` | 3D globe with destination explorer |
| `/destinations` | Destination gallery |
| `/model` | 3D model viewer |
| `/api/ask` | `POST` — AI chat endpoint |
| `/api/itinerary` | `POST` — itinerary generation |
| `/healthz` | Liveness probe |
| `/readyz` | Readiness probe |
| `/metrics` | Prometheus metrics |
| `/docs` | Swagger UI |

---

## Make Commands

```bash
make help          # List everything
make dev           # Run locally on :8080
make test          # Run pytest
make lint          # Run flake8
make docker-build  # Build the Docker image
make docker-run    # Run container on :8080
make compose-up    # Start app + Prometheus + Grafana + Loki
make compose-down  # Tear it all down
make clean         # Remove caches and build artifacts
```

---

## Running with Docker

```bash
# Just the app
make docker-build && make docker-run

# Full stack (app + Prometheus + Grafana + Loki + Promtail)
make compose-up
```

Once the stack is up:
- App → http://localhost:8080
- Prometheus → http://localhost:9090
- Grafana → http://localhost:3000 (admin / secret)

---

## Kubernetes Deployment

Uses Kustomize with dev/prod overlays and ArgoCD for GitOps.

```bash
# Spin up a local cluster
./scripts/kind-create.sh

# Set up secrets
cp deploy/base/secret-template.yaml deploy/base/secret.yaml
# Edit secret.yaml with your API keys
kubectl apply -f deploy/base/secret.yaml

# Build, load, deploy
make docker-build
kind load docker-image airports-ai:latest --name airports-ai-local
kubectl apply -k deploy/overlays/dev

# Access
kubectl port-forward svc/airports-ai 8080:8080
```

### ArgoCD (GitOps)

```bash
./scripts/argocd-install.sh
# Update the repoURL in deploy/argocd-application.yaml, then:
kubectl apply -f deploy/argocd-application.yaml
# ArgoCD auto-syncs every 3 minutes from the main branch
```

---

## Observability

The app exposes Prometheus metrics (`request_count`, `request_latency_seconds`) on `/metrics`. Structured JSON logs go to stdout for Loki/Promtail to pick up.

### Deploy Monitoring to K8s

```bash
./scripts/monitoring-install.sh

kubectl port-forward -n monitoring svc/prometheus 9090:9090
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

### Useful PromQL

```promql
# Requests per second
sum(rate(request_count[1m]))

# P95 latency
histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le))

# Error rate
sum(rate(request_count{status_code=~"5.."}[5m])) / sum(rate(request_count[5m]))
```

Alerts fire on error rate > 5% or P95 latency > 1s (sustained for 5 minutes).

---

## CI/CD

GitHub Actions runs on push to `main`/`develop` and on PRs:

1. **Lint** — flake8
2. **Test** — pytest
3. **Dependency scan** — pip-audit
4. **Docker build** — multi-stage image
5. **Container scan** — Trivy (CRITICAL/HIGH)

Results show up in the GitHub Security tab.

---

## Security

- **Rate limiting** — per-IP limits on all endpoints (Flask-Limiter)
- **Input validation** — prompt length caps, field sanitization, control character stripping
- **XSS prevention** — HTML sanitization on all LLM output before DOM insertion, plus Content-Security-Policy headers
- **History role whitelisting** — only `user` and `assistant` roles accepted (blocks system prompt injection)
- **Security headers** — CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Container security** — non-root user, read-only root filesystem, all capabilities dropped
- **Secrets** — API keys via env vars / K8s Secrets, never hardcoded

---

## Project Structure

```
├── app.py                   # Flask app, middleware, security headers
├── ai_routes.py             # /api/ask and /api/itinerary endpoints
├── cache.py                 # SQLite prompt/response cache
├── limiter_config.py        # Rate limiting setup
├── Dockerfile               # Multi-stage build, non-root
├── docker-compose.yml       # App + Prometheus + Grafana + Loki
├── Makefile                 # Dev commands
├── RUNBOOK.md               # Ops playbook
│
├── static/                  # JS, CSS, assets
├── templates/               # Jinja2 HTML templates
├── tests/                   # pytest tests
│
├── deploy/
│   ├── base/                # K8s manifests (deployment, service, configmap)
│   ├── overlays/dev/        # Dev patches
│   ├── overlays/prod/       # Prod patches
│   ├── monitoring/          # Prometheus + Grafana manifests
│   └── argocd-application.yaml
│
├── scripts/                 # Cluster and monitoring setup scripts
├── config/                  # Prometheus, Loki, Promtail configs
└── .github/workflows/ci.yml # CI pipeline
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | API key for the LLM provider |
| `MAPTILER_KEY` | No | For the 3D globe map tiles |
| `GRAFANA_PASSWORD` | No | Grafana admin password |

---

## Testing

```bash
make test                              # Run all tests
pytest tests/test_security.py -v       # Security tests only
pytest tests/ --cov=. --cov-report=html # With coverage
```

---

## Operations

See [RUNBOOK.md](RUNBOOK.md) for troubleshooting, rollback procedures, and alert response playbooks.

```bash
kubectl get pods                                    # Check status
kubectl logs -f <pod-name> | jq                     # Stream logs
kubectl rollout undo deployment/airports-ai         # Rollback
kubectl scale deployment airports-ai --replicas=3   # Scale
```
