# OpenQQuantify - AI Travel Platform

**A platform-engineered AI travel concierge demonstrating enterprise-grade infrastructure patterns**

[![CI Pipeline](https://github.com/YOUR_USERNAME/airports.ai.OQQ/workflows/CI%20Pipeline/badge.svg)](https://github.com/YOUR_USERNAME/airports.ai.OQQ/actions)

---

## 🌟 Platform Engineering Features

This project showcases production-ready platform engineering practices:

- ✅ **Service Standardization** - Consistent port (8080), health endpoints, structured logging
- ✅ **Developer Experience** - One-command setup with comprehensive Makefile
- ✅ **CI/CD Pipeline** - Automated testing, linting, security scanning with GitHub Actions
- ✅ **GitOps** - Declarative Kubernetes deployment with ArgoCD auto-sync
- ✅ **Observability** - Prometheus metrics, Grafana dashboards, alerting, runbooks
- ✅ **Infrastructure as Code** - Kubernetes manifests with Kustomize overlays
- ✅ **Security** - Container scanning (Trivy), dependency scanning (pip-audit), non-root containers

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Traffic                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Ingress/Nginx  │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │               │
        ▼              ▼               ▼
   ┌────────┐    ┌────────┐     ┌────────┐
   │  Pod1  │    │  Pod2  │     │  Pod3  │
   │ :8080  │    │ :8080  │     │ :8080  │
   └───┬────┘    └───┬────┘     └───┬────┘
       │             │               │
       │  /healthz  /readyz  /metrics
       │             │               │
       └─────────────┼───────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │               │
      ▼              ▼               ▼
 ┌─────────┐  ┌────────────┐  ┌──────────┐
 │ OpenRouter  │ Prometheus │  │ SQLite   │
 │  AI API  │  │  Scraper   │  │  Cache   │
 └─────────┘  └─────┬──────┘  └──────────┘
                     │
                     ▼
              ┌────────────┐
              │  Grafana   │
              │ Dashboards │
              └────────────┘
```

---

## 🚀 Quick Start

### Local Development (Golden Path)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/airports.ai.OQQ.git
cd airports.ai.OQQ

# 2. One command to start developing
make dev
```

That's it! The app will:
- Create a virtual environment
- Install dependencies
- Start on http://localhost:8080

### Available Endpoints

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:8080/` | Main application UI |
| `http://localhost:8080/healthz` | Liveness probe (Kubernetes) |
| `http://localhost:8080/readyz` | Readiness probe (Kubernetes) |
| `http://localhost:8080/metrics` | Prometheus metrics |
| `http://localhost:8080/docs` | OpenAPI/Swagger docs |

---

## 🛠️ Developer Commands

```bash
make help          # Show all available commands
make install       # Create venv and install dependencies
make dev           # Run app locally with hot reload (port 8080)
make test          # Run pytest tests
make lint          # Run code linting (flake8)
make docker-build  # Build Docker image
make docker-run    # Run Docker container (port 8080)
make compose-up    # Start full observability stack (app + Prometheus + Grafana)
make clean         # Remove cache, pyc files, and build artifacts
```

---

## 🐳 Docker Quick Start

```bash
# Build the image
make docker-build

# Run the container
make docker-run

# Or use full observability stack
make compose-up
```

**Observability Stack Includes:**
- **App** - http://localhost:8080
- **Prometheus** - http://localhost:9090
- **Grafana** - http://localhost:3000 (admin/secret)
- **Loki** - http://localhost:3100

---

## ☸️ Kubernetes Deployment

### Prerequisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) (for local cluster)
- [kustomize](https://kustomize.io/) (built into kubectl)

### Local Kubernetes with kind

```bash
# 1. Create local Kubernetes cluster
./scripts/kind-create.sh

# 2. Create secrets (edit with your values first)
cp deploy/base/secret-template.yaml deploy/base/secret.yaml
# Edit deploy/base/secret.yaml with your actual API keys
kubectl apply -f deploy/base/secret.yaml

# 3. Build and load image into kind
make docker-build
kind load docker-image airports-ai:latest --name airports-ai-local

# 4. Deploy application
kubectl apply -k deploy/overlays/dev

# 5. Wait for pod to be ready
kubectl get pods -w

# 6. Access the app
kubectl port-forward svc/airports-ai 8080:8080
# Open http://localhost:8080
```

### Verify Deployment

```bash
# Check health
kubectl get pods
kubectl describe pod <pod-name>

# Check health endpoint
kubectl port-forward svc/airports-ai 8080:8080
curl http://localhost:8080/healthz
# Expected: {"status": "healthy"}

# View logs (JSON formatted)
kubectl logs -f <pod-name> | jq

# Check metrics
curl http://localhost:8080/metrics
```

---

## 📊 Observability Stack

### Deploy Monitoring

```bash
# Deploy Prometheus and Grafana to Kubernetes
./scripts/monitoring-install.sh

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open http://localhost:9090

# Access Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
# Open http://localhost:3000 (admin/admin)
```

### Grafana Dashboard

**Dashboard:** "Airports AI - Platform Metrics"

**Panels:**
- **Requests Per Second** - Total RPS across all endpoints
- **Request Latency** - P50, P95, P99 latency percentiles
- **Error Rate** - 4xx and 5xx error rates
- **Requests by Endpoint** - Traffic breakdown by endpoint

### Prometheus Queries

```promql
# RPS
sum(rate(request_count[1m]))

# Error rate
sum(rate(request_count{status_code=~"5.."}[5m])) / sum(rate(request_count[5m]))

# P95 latency
histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le))

# Requests by endpoint
sum(rate(request_count[1m])) by (endpoint)
```

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| HighErrorRate | Error rate > 5% for 5 minutes | Warning |
| HighLatency | P95 latency > 1s for 5 minutes | Warning |

---

## 🔄 GitOps with ArgoCD

### Install ArgoCD

```bash
# Install ArgoCD in your kind cluster
./scripts/argocd-install.sh

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Access ArgoCD UI
kubectl port-forward -n argocd svc/argocd-server 8081:443
# Open https://localhost:8081 (username: admin)
```

### Deploy Application via ArgoCD

```bash
# 1. Update repository URL in deploy/argocd-application.yaml
vim deploy/argocd-application.yaml
# Change: repoURL: https://github.com/YOUR_USERNAME/airports.ai.OQQ.git

# 2. Apply ArgoCD Application
kubectl apply -f deploy/argocd-application.yaml

# 3. Watch sync status
kubectl get applications -n argocd

# 4. ArgoCD will automatically deploy and sync every 3 minutes
```

### GitOps Workflow

```bash
# 1. Make changes to Kubernetes manifests
vim deploy/base/deployment.yaml

# 2. Commit and push
git add deploy/
git commit -m "feat: increase replicas to 3"
git push origin main

# 3. ArgoCD auto-syncs within 3 minutes
# Or manually sync: argocd app sync airports-ai-dev

# 4. Verify deployment
kubectl get pods -w
```

---

## 🔒 CI/CD Pipeline

### GitHub Actions Workflow

**Trigger:** Push to `main`/`develop` or Pull Request

**Jobs:**
1. **Lint** - Run flake8 on Python code
2. **Test** - Run pytest tests
3. **Security Scan (Dependencies)** - pip-audit for vulnerability scanning
4. **Build** - Build Docker container image
5. **Security Scan (Container)** - Trivy for container vulnerability scanning

**Security Gates:**
- Fails on HIGH/CRITICAL vulnerabilities in dependencies
- Scans container for vulnerabilities
- Reports results to GitHub Security tab

### Run CI Locally

```bash
# Lint
make lint

# Test
make test

# Build
make docker-build

# Security scan (requires docker and trivy)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image airports-ai:latest
```

---

## 📖 Runbook & Operations

**See [RUNBOOK.md](RUNBOOK.md) for:**
- Troubleshooting guides
- Common failure modes
- Rollback procedures
- Alert response playbooks
- Scaling procedures

### Quick Operations Reference

```bash
# Check health
kubectl get pods
kubectl logs -f <pod-name>

# Scale replicas
kubectl scale deployment airports-ai --replicas=3

# Rollback deployment
kubectl rollout undo deployment/airports-ai

# View metrics
kubectl port-forward svc/airports-ai 8080:8080
curl http://localhost:8080/metrics

# Access Grafana dashboard
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

---

## 🏗️ Project Structure

```
.
├── app.py                          # Main Flask application
├── ai_routes.py                    # AI API routes
├── cache.py                        # SQLite caching layer
├── limiter_config.py               # Rate limiting config
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Multi-stage container build
├── docker-compose.yml              # Local observability stack
├── Makefile                        # Developer experience commands
├── RUNBOOK.md                      # Operational playbook
│
├── .github/workflows/
│   └── ci.yml                      # GitHub Actions CI pipeline
│
├── deploy/
│   ├── base/                       # Base Kubernetes manifests
│   │   ├── deployment.yaml         # App deployment
│   │   ├── service.yaml            # App service
│   │   ├── configmap.yaml          # App config
│   │   ├── kustomization.yaml      # Kustomize base
│   │   └── secret-template.yaml    # Secret template
│   │
│   ├── overlays/
│   │   ├── dev/                    # Dev environment
│   │   │   ├── kustomization.yaml
│   │   │   └── deployment-patch.yaml
│   │   └── prod/                   # Prod environment
│   │       └── kustomization.yaml
│   │
│   ├── monitoring/                 # Observability stack
│   │   ├── namespace.yaml
│   │   ├── prometheus-config.yaml
│   │   ├── prometheus-deployment.yaml
│   │   ├── grafana-deployment.yaml
│   │   ├── grafana-datasources.yaml
│   │   ├── grafana-dashboards-config.yaml
│   │   └── grafana-dashboards.yaml
│   │
│   └── argocd-application.yaml     # ArgoCD app definition
│
└── scripts/
    ├── kind-create.sh              # Create kind cluster
    ├── kind-destroy.sh             # Destroy kind cluster
    ├── argocd-install.sh           # Install ArgoCD
    └── monitoring-install.sh       # Install monitoring stack
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter AI API key for travel recommendations |
| `MAPTILER_KEY` | No | MapTiler API key for map visualization |
| `GRAFANA_PASSWORD` | No | Grafana admin password (default: admin) |

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_chat_context.py -v
```

---

## 📊 Platform Metrics

**Definition of Done for Each Phase:**
- ✅ Phase 1: Service Standardization (port 8080, health endpoints, JSON logs)
- ✅ Phase 2: Developer Experience (Makefile, one-command setup)
- ✅ Phase 3: CI/CD (GitHub Actions, security scanning)
- ✅ Phase 4: GitOps (kind, Kustomize, ArgoCD)
- ✅ Phase 5: Observability (Prometheus, Grafana, alerts, runbook)
- ✅ Phase 6: Documentation (README, architecture, evidence)

---

## 🎯 Platform Engineering Concepts Demonstrated

1. **Service Standardization** - Consistent interfaces (ports, health checks, metrics)
2. **Golden Path** - One-command developer onboarding (`make dev`)
3. **Infrastructure as Code** - Declarative Kubernetes manifests
4. **GitOps** - Git as single source of truth for infrastructure
5. **Observability** - Metrics, logging, alerting, dashboards
6. **Security** - Automated vulnerability scanning in CI/CD
7. **Reliability** - Health probes, auto-scaling, self-healing
8. **Developer Experience** - Fast feedback loops, clear documentation

---

## 🤝 Contributing

See [PLATFORM_TODO.md](https://github.com/YOUR_USERNAME/airports.ai.OQQ/blob/main/.gemini/antigravity/brain/9127960d-cea3-4df7-815b-2140cbf9f909/PLATFORM_TODO.md) for the complete platform engineering checklist.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

---

## 📧 Contact

**Platform Team:** platform-team@example.com  
**Issues:** https://github.com/YOUR_USERNAME/airports.ai.OQQ/issues

---

**Built with ❤️ demonstrating enterprise platform engineering patterns**
