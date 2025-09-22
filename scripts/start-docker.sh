#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== STARTING PICKERWHEEL DOCKER CONTAINER ===${NC}"
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

# Get the host IP address
HOST_IP=$(hostname -I | awk '{print $1}')
if [[ -z "$HOST_IP" ]]; then
    # Try alternative methods
    HOST_IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1)
    if [[ -z "$HOST_IP" ]]; then
        HOST_IP="<your-ip-address>"
    fi
fi

echo -e "${YELLOW}Building and starting Docker container...${NC}"
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PickerWheel Docker container started successfully!${NC}"
    echo ""
    echo -e "${YELLOW}=== ACCESS INFORMATION ===${NC}"
    echo ""
    echo -e "${GREEN}Local Access:${NC}"
    echo -e "Main Contest:    ${BLUE}http://localhost:8080${NC}"
    echo -e "Admin Panel:     ${BLUE}http://localhost:8080/admin.html${NC}"
    echo ""
    echo -e "${GREEN}Network Access (for other devices):${NC}"
    echo -e "Main Contest:    ${BLUE}http://$HOST_IP:8080${NC}"
    echo -e "Admin Panel:     ${BLUE}http://$HOST_IP:8080/admin.html${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} If you have a firewall enabled, make sure port 8080 is allowed."
    echo ""
    echo -e "${GREEN}Admin Credentials:${NC}"
    echo -e "Password: ${BLUE}myTAdmin2025${NC} (Use Ctrl+Alt+A to access admin panel)"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "Stop container:   ${BLUE}./scripts/stop-docker.sh${NC}"
    echo -e "View logs:        ${BLUE}docker-compose logs -f${NC}"
    echo -e "Network info:     ${BLUE}./scripts/show-network-info.sh${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to start PickerWheel Docker container${NC}"
    echo "Please check the error messages above."
fi
