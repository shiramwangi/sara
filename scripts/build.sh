#!/bin/bash

# Sara AI Receptionist Build Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="sara-ai-receptionist"
IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-your-registry.com}"

echo -e "${GREEN}Building Sara AI Receptionist Docker image...${NC}"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building image: ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .

# Tag for registry
if [ "$REGISTRY" != "your-registry.com" ]; then
    echo -e "${YELLOW}Tagging image for registry: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}${NC}"
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}
fi

# Show image information
echo -e "${YELLOW}Image information:${NC}"
docker images | grep ${IMAGE_NAME}

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}To run locally: docker run -p 8000:8000 ${IMAGE_NAME}:${IMAGE_TAG}${NC}"
if [ "$REGISTRY" != "your-registry.com" ]; then
    echo -e "${YELLOW}To push to registry: docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}${NC}"
fi
