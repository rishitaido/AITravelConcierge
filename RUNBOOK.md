# Operational Runbook - Airports AI Platform

## Overview

This runbook provides operational procedures for the Airports AI platform. Use this guide for troubleshooting, debugging, and recovering from common failure scenarios.

## Quick Reference

**App:** Airports AI Travel Concierge  
**Port:** 8080  
**Health Check:** `/healthz`  
**Readiness Check:** `/readyz`  
**Metrics:** `/metrics`  
**Namespace:** `default` (app), `monitoring` (observability)

---

## Common Operations

### Check Application Health

```bash
# Local development
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz

# Kubernetes
kubectl port-forward svc/airports-ai 8080:8080
curl http://localhost:8080/healthz
```

**Expected Response:**
```json
{"status": "healthy"}
```

---

### View Application Logs

**Local development:**
```bash
# Logs go to stdout with JSON formatting
make dev

# Or directly
python app.py 2>&1 | jq
```

**Kubernetes:**
```bash
# Get pod name
kubectl get pods -l app=airports-ai

# Follow logs (JSON formatted)
kubectl logs -f <pod-name> | jq

# Last 100 lines
kubectl logs --tail=100 <pod-name>

# Logs from all pods
kubectl logs -l app=airports-ai --all-containers=true
```

**Log Fields:**
- `timestamp`: Unix timestamp
- `level`: INFO, WARNING, ERROR
- `message`: Log message
- `endpoint`: HTTP endpoint (if during request)
- `method`: HTTP method (if during request)
- `status_code`: Response code (if during request)
- `latency_seconds`: Request latency (if during request)

---

### Check Metrics

**Local:**
```bash
curl http://localhost:8080/metrics
```

**Kubernetes:**
```bash
kubectl port-forward svc/airports-ai 8080:8080
curl http://localhost:8080/metrics
```

**Key Metrics:**
- `request_count_total` - Total HTTP requests by method and endpoint
- `request_latency_seconds` - Request latency histogram
- `request_latency_seconds_bucket` - Latency buckets for percentile calculation

---

### Access Prometheus

```bash
# Port-forward Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Open in browser
open http://localhost:9090
```

**Useful Queries:**
```promql
# RPS (requests per second)
sum(rate(request_count[1m]))

# Error rate
sum(rate(request_count{status_code=~"5.."}[5m])) / sum(rate(request_count[5m]))

# P95 latency
histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le))

# Requests by endpoint
sum(rate(request_count[1m])) by (endpoint)
```

---

### Access Grafana

```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Open in browser (login: admin/admin)
open http://localhost:3000
```

**Dashboard:** "Airports AI - Platform Metrics"  
**Location:** Home → Dashboards

---

## Troubleshooting

### Problem: App Won't Start

**Symptoms:**
- Pod in `CrashLoopBackOff` state
- Health check failing immediately

**Debug Steps:**

1. **Check pod status:**
   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   ```

2. **Check logs:**
   ```bash
   kubectl logs <pod-name>
   kubectl logs <pod-name> --previous  # Previous crash
   ```

3. **Common causes:**
   - Missing environment variables (check secrets)
   - Port already in use
   - Import errors (missing dependencies)
   - Invalid configuration

4. **Verify secrets exist:**
   ```bash
   kubectl get secret airports-ai-secrets
   kubectl describe secret airports-ai-secrets
   ```

5. **Create secrets if missing:**
   ```bash
   kubectl create secret generic airports-ai-secrets \
     --from-literal=openrouter-api-key=YOUR_KEY \
     --from-literal=maptiler-key=YOUR_KEY \
     --from-literal=grafana-password=admin
   ```

---

### Problem: High Latency

**Symptoms:**
- `HighLatency` alert firing
- Slow response times
- Timeouts

**Debug Steps:**

1. **Check current latency:**
   ```bash
   # In Prometheus
   histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le, endpoint))
   ```

2. **Identify slow endpoints:**
   ```bash
   # Group by endpoint
   histogram_quantile(0.95, sum(rate(request_latency_seconds_bucket[5m])) by (le, endpoint))
   ```

3. **Check external dependencies:**
   - OpenRouter API response time
   - Database queries (if applicable)
   - Network connectivity

4. **Check pod resources:**
   ```bash
   kubectl top pod <pod-name>
   kubectl describe pod <pod-name> | grep -A 5 "Limits"
   ```

5. **Scale if needed:**
   ```bash
   # Increase replicas
   kubectl scale deployment airports-ai --replicas=3
   
   # Or edit deployment
   kubectl edit deployment airports-ai
   ```

---

### Problem: High Error Rate

**Symptoms:**
- `HighErrorRate` alert firing
- Many 5xx responses
- Users reporting errors

**Debug Steps:**

1. **Check error rate:**
   ```bash
   # In Prometheus
   sum(rate(request_count{status_code=~"5.."}[5m])) / sum(rate(request_count[5m]))
   ```

2. **Identify error endpoints:**
   ```bash
   sum(rate(request_count{status_code=~"5.."}[5m])) by (endpoint)
   ```

3. **Check application logs:**
   ```bash
   kubectl logs -l app=airports-ai | jq 'select(.level == "ERROR")'
   ```

4. **Common causes:**
   - **External API failures:** Check OpenRouter API status
   - **Missing secrets:** Verify environment variables
   - **Resource limits:** CPU/memory throttling
   - **Database issues:** Connection pool exhaustion

5. **Verify external dependencies:**
   ```bash
   # Test OpenRouter API manually
   curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        https://openrouter.ai/api/v1/models
   ```

---

### Problem: Pod Not Ready

**Symptoms:**
- Pod stuck in `0/1 Ready` state
- Readiness probe failing

**Debug Steps:**

1. **Check readiness probe:**
   ```bash
   kubectl describe pod <pod-name> | grep -A 10 "Readiness"
   ```

2. **Test readiness endpoint:**
   ```bash
   kubectl port-forward <pod-name> 8080:8080
   curl http://localhost:8080/readyz
   ```

3. **Check events:**
   ```bash
   kubectl get events --sort-by='.lastTimestamp' | grep <pod-name>
   ```

4. **Common causes:**
   - App startup delay (increase `initialDelaySeconds`)
   - Database connection failure
   - External dependency timeout

---

## Rollback Procedure

### GitOps Rollback (Recommended)

When using ArgoCD, rollback via Git:

```bash
# 1. Find the commit to revert
git log --oneline deploy/

# 2. Revert the problematic commit
git revert <commit-hash>

# 3. Push to trigger ArgoCD sync
git push origin main

# 4. Watch ArgoCD sync the rollback
kubectl get applications -n argocd
```

**ArgoCD will automatically:**
- Detect the Git change
- Sync the cluster to the reverted state
- Update pod deployments

---

### Manual Rollback

If not using ArgoCD:

```bash
# 1. Check deployment history
kubectl rollout history deployment/airports-ai

# 2. Rollback to previous revision
kubectl rollout undo deployment/airports-ai

# 3. Rollback to specific revision
kubectl rollout undo deployment/airports-ai --to-revision=2

# 4. Watch rollout status
kubectl rollout status deployment/airports-ai
```

---

## Alerts

### HighErrorRate

**Trigger:** Error rate > 5% for 5 minutes  
**Severity:** Warning

**Response:**
1. Check [High Error Rate](#problem-high-error-rate) troubleshooting
2. Verify external API status
3. Check recent deployments (potential bad release)
4. Consider rollback if necessary

---

### HighLatency

**Trigger:** P95 latency > 1 second for 5 minutes  
**Severity:** Warning

**Response:**
1. Check [High Latency](#problem-high-latency) troubleshooting
2. Identify slow endpoints
3. Check resource usage
4. Scale if CPU/memory constrained

---

## Deployment Process

### Local Development

```bash
# 1. Make changes
code app.py

# 2. Test locally
make dev

# 3. Run tests
make test

# 4. Lint code
make lint

# 5. Commit
git add .
git commit -m "feat: add new feature"
git push
```

---

### Production Deployment (GitOps)

```bash
# 1. Update image tag in kustomization
vim deploy/overlays/prod/kustomization.yaml

# 2. Commit and push
git add deploy/
git commit -m "release: bump to v1.2.3"
git push origin main

# 3. ArgoCD auto-syncs within 3 minutes
# Or manually sync:
argocd app sync airports-ai-prod

# 4. Watch deployment
kubectl get pods -w

# 5. Verify health
kubectl port-forward svc/airports-ai 8080:8080
curl http://localhost:8080/healthz
```

---

## Scaling

### Horizontal Scaling

```bash
# Scale replicas
kubectl scale deployment airports-ai --replicas=5

# Auto-scaling (requires metrics-server)
kubectl autoscale deployment airports-ai \
  --min=2 \
  --max=10 \
  --cpu-percent=70
```

### Vertical Scaling

Edit resource limits in `deploy/base/deployment.yaml`:

```yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

---

## Monitoring Best Practices

1. **Check Grafana dashboard daily**
2. **Set up alert notifications** (Slack, PagerDuty)
3. **Review error logs weekly**
4. **Monitor external API quotas**
5. **Track deployment frequency and MTTR**

---

## Emergency Contacts

**Platform Team:** platform-team@example.com  
**On-Call:** Use PagerDuty rotation  
**Escalation:** engineering-leads@example.com

---

## Common Failure Modes

| Failure Mode | Symptoms | Root Cause | Fix |
|--------------|----------|------------|-----|
| API Rate Limit | 429 errors | OpenRouter quota exceeded | Implement backoff, increase limits |
| OOM Kill | Pod restarts, OutOfMemory | Memory leak or spike | Increase limits, fix leak |
| DNS Resolution | Connection timeouts | CoreDNS issues | Restart CoreDNS pods |
| Image Pull | ImagePullBackOff | Registry auth failure | Update imagePullSecrets |
| Secret Missing | App crashes on startup | Secret not created | Apply secret manifest |

---

**Last Updated:** 2026-02-17  
**Maintained By:** Platform Engineering Team  
**Version:** 1.0
