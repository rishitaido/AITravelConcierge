#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="airports-ai-local"

echo "🚀 Creating kind cluster: ${CLUSTER_NAME}"

# Create kind cluster with ingress support
cat <<EOF | kind create cluster --name ${CLUSTER_NAME} --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
EOF

echo ""
echo "✅ Cluster created successfully!"
echo ""
echo "📦 Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo ""
echo "⏳ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=90s

echo ""
echo "✅ Kind cluster is ready!"
echo ""
echo "Cluster info:"
kubectl cluster-info --context kind-${CLUSTER_NAME}
echo ""
echo "Nodes:"
kubectl get nodes
echo ""
echo "Next steps:"
echo "  1. Deploy app: kubectl apply -k deploy/overlays/dev"
echo "  2. Install ArgoCD: ./scripts/argocd-install.sh"
echo "  3. Port-forward to access: kubectl port-forward svc/airports-ai 8080:8080"
