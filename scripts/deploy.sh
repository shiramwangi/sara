#!/bin/bash

# Sara AI Receptionist Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="sara"
IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-your-registry.com}"

echo -e "${GREEN}Starting Sara AI Receptionist deployment...${NC}"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${YELLOW}Deploying to namespace: ${NAMESPACE}${NC}"
echo -e "${YELLOW}Using image: ${REGISTRY}/sara-ai-receptionist:${IMAGE_TAG}${NC}"

# Create namespace if it doesn't exist
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply Kubernetes manifests
echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"

# Apply in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for deployments to be ready
echo -e "${YELLOW}Waiting for deployments to be ready...${NC}"

kubectl wait --for=condition=available --timeout=300s deployment/postgres -n ${NAMESPACE}
kubectl wait --for=condition=available --timeout=300s deployment/redis -n ${NAMESPACE}
kubectl wait --for=condition=available --timeout=300s deployment/sara-backend -n ${NAMESPACE}

# Check pod status
echo -e "${YELLOW}Checking pod status...${NC}"
kubectl get pods -n ${NAMESPACE}

# Get service information
echo -e "${YELLOW}Service information:${NC}"
kubectl get services -n ${NAMESPACE}

# Get ingress information
echo -e "${YELLOW}Ingress information:${NC}"
kubectl get ingress -n ${NAMESPACE}

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${YELLOW}To check logs: kubectl logs -f deployment/sara-backend -n ${NAMESPACE}${NC}"
echo -e "${YELLOW}To port forward: kubectl port-forward service/sara-service 8000:8000 -n ${NAMESPACE}${NC}"
