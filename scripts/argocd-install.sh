#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Installing ArgoCD..."

# Create argocd namespace
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
echo "📦 Installing ArgoCD manifests..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "⏳ Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=available --timeout=300s \
  deployment/argocd-server \
  deployment/argocd-repo-server \
  deployment/argocd-applicationset-controller \
  -n argocd

echo ""
echo "✅ ArgoCD installed successfully!"
echo ""
echo "🔐 Getting initial admin password..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ArgoCD Access Info                        ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║ Username: admin                                            ║"
echo "║ Password: ${ARGOCD_PASSWORD}                               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "To access ArgoCD UI:"
echo "  1. Port-forward: kubectl port-forward svc/argocd-server -n argocd 8081:443"
echo "  2. Open browser: https://localhost:8081"
echo "  3. Login with credentials above"
echo ""
echo "To install the ArgoCD CLI (optional):"
echo "  brew install argocd"
echo ""
echo "Next steps:"
echo "  1. Apply ArgoCD Application: kubectl apply -f deploy/argocd-application.yaml"
echo "  2. Watch sync status: kubectl get applications -n argocd"
