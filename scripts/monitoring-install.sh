#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying monitoring stack to Kubernetes..."

# Deploy Prometheus (includes namespace, config, deployment, service)
echo "📊 Deploying Prometheus..."
kubectl apply -f deploy/monitoring/prometheus.yaml

# Deploy Grafana (includes secret template, datasources, dashboards, deployment, service)
echo "📈 Deploying Grafana..."
kubectl apply -f deploy/monitoring/grafana.yaml

# Wait for deployments
echo "⏳ Waiting for Prometheus to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/prometheus -n monitoring

echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=available --timeout=120s deployment/grafana -n monitoring

echo ""
echo "✅ Monitoring stack deployed successfully!"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Monitoring Stack Access Info                  ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║ Prometheus:                                                ║"
echo "║   kubectl port-forward -n monitoring svc/prometheus 9090   ║"
echo "║   http://localhost:9090                                    ║"
echo "║                                                            ║"
echo "║ Grafana:                                                   ║"
echo "║   kubectl port-forward -n monitoring svc/grafana 3000      ║"
echo "║   http://localhost:3000                                    ║"
echo "║   Username: admin                                          ║"
echo "║   Password: (from monitoring-secrets Secret)               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Deploy app: kubectl apply -k deploy/overlays/dev"
echo "  2. Access Grafana and view 'Airports AI - Platform Metrics' dashboard"
echo "  3. View Prometheus alerts: http://localhost:9090/alerts"
