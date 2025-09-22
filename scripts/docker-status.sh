#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== PICKERWHEEL DOCKER CONTAINER STATUS ===${NC}"
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

# Check container status
echo -e "${YELLOW}Container Status:${NC}"
docker-compose ps

echo ""
echo -e "${YELLOW}Container Resource Usage:${NC}"
docker stats --no-stream $(docker-compose ps -q)

# Check if container is running
CONTAINER_RUNNING=$(docker-compose ps -q)
if [ -n "$CONTAINER_RUNNING" ]; then
    # Get the host IP address
    HOST_IP=$(hostname -I | awk '{print $1}')
    if [[ -z "$HOST_IP" ]]; then
        # Try alternative methods
        HOST_IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1)
        if [[ -z "$HOST_IP" ]]; then
            HOST_IP="<your-ip-address>"
        fi
    fi
    
    echo ""
    echo -e "${GREEN}Access URLs:${NC}"
    echo -e "Main Contest:    ${BLUE}http://$HOST_IP:9080${NC}"
    echo -e "Admin Panel:     ${BLUE}http://$HOST_IP:9080/admin.html${NC}"
fi
