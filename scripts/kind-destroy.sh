#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="airports-ai-local"

echo "🛑 Destroying kind cluster: ${CLUSTER_NAME}"

kind delete cluster --name ${CLUSTER_NAME}

echo ""
echo "✅ Cluster destroyed successfully!"
echo ""
echo "Remaining clusters:"
kind get clusters || echo "No clusters remaining"
