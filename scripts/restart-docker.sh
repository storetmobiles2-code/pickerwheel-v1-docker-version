#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== RESTARTING PICKERWHEEL DOCKER CONTAINER ===${NC}"
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

# Restart container
echo -e "${YELLOW}Restarting Docker container...${NC}"
docker-compose restart

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PickerWheel Docker container restarted successfully!${NC}"
    
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
    echo -e "${GREEN}You can access the application at:${NC}"
    echo -e "${BLUE}http://$HOST_IP:9080${NC}"
else
    echo -e "${RED}❌ Failed to restart PickerWheel Docker container${NC}"
    echo "Please check the error messages above."
fi
