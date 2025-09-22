#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== PICKERWHEEL DOCKER CONTAINER LOGS ===${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if container is running
CONTAINER_RUNNING=$(docker-compose ps -q)
if [ -z "$CONTAINER_RUNNING" ]; then
    echo -e "${RED}Error: PickerWheel Docker container is not running${NC}"
    echo -e "Please start the container with ${BLUE}./scripts/start-docker.sh${NC}"
    exit 1
fi

# Show logs
echo -e "${YELLOW}Showing logs (press Ctrl+C to exit)...${NC}"
echo ""
docker-compose logs -f
