#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IMPORTING PICKERWHEEL DOCKER IMAGE ===${NC}"
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

# Define the tarfile name
TARFILE="pickerwheel.tar"

# Check if the tarfile exists
if [ ! -f "$TARFILE" ]; then
    echo -e "${RED}Error: $TARFILE not found${NC}"
    echo -e "Please make sure the file is in the current directory: ${BLUE}$(pwd)${NC}"
    exit 1
fi

# Import the Docker image
echo -e "${YELLOW}Importing Docker image from $TARFILE...${NC}"
docker load -i "$TARFILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image imported successfully!${NC}"
    echo ""
    echo -e "${YELLOW}=== NEXT STEPS ===${NC}"
    echo ""
    echo -e "1. Start the Docker container: ${BLUE}./scripts/start-docker.sh${NC}"
    echo -e "2. Access the application: ${BLUE}http://localhost:8080${NC}"
    echo -e "3. Admin access: Use Ctrl+Alt+A and password ${BLUE}myTAdmin2025${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to import Docker image${NC}"
    echo "Please check the error messages above."
fi
