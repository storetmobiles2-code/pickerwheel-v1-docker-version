#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== IMPORTING AND STARTING PICKERWHEEL DOCKER CONTAINER ===${NC}"
echo ""

# Define the tarfile name
TARFILE="pickerwheel.tar"

# Check if the tarfile exists
if [ -f "$TARFILE" ]; then
    echo -e "${YELLOW}Found Docker image file: $TARFILE${NC}"
    echo -e "${YELLOW}Importing Docker image...${NC}"
    
    # Import the Docker image
    ./scripts/import-docker-image.sh
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to import Docker image${NC}"
        echo "Please check the error messages above."
        exit 1
    fi
else
    echo -e "${YELLOW}Docker image file not found. Will build from source.${NC}"
fi

# Start the Docker container
echo -e "${YELLOW}Starting Docker container...${NC}"
./scripts/start-docker.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to start Docker container${NC}"
    echo "Please check the error messages above."
    exit 1
fi

echo -e "${GREEN}✅ PickerWheel Docker container imported and started successfully!${NC}"
