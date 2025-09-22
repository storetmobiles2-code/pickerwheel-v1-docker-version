#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== EXPORTING PICKERWHEEL DOCKER IMAGE ===${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker from https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Export to the current directory
EXPORT_DIR="."
# No need to create directory as we're using the current one

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker-compose build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi

# Get the image name
IMAGE_NAME="pickerwheel-v4-docker-version-pickerwheel"

# Export the Docker image
TARFILE="pickerwheel.tar"
echo -e "${YELLOW}Exporting Docker image to $EXPORT_DIR/$TARFILE...${NC}"
docker save "$IMAGE_NAME" -o "$EXPORT_DIR/$TARFILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image exported successfully!${NC}"
    echo ""
    echo -e "${YELLOW}=== EXPORT INFORMATION ===${NC}"
    echo ""
    echo -e "Image file: ${BLUE}$EXPORT_DIR/$TARFILE${NC}"
    echo -e "Image size: ${BLUE}$(du -h "$EXPORT_DIR/$TARFILE" | cut -f1)${NC}"
    echo ""
    echo -e "${YELLOW}=== WINDOWS IMPORT INSTRUCTIONS ===${NC}"
    echo ""
    echo -e "1. Copy ${BLUE}$TARFILE${NC} to your Windows machine in the same directory as the scripts"
    echo -e "2. Open Command Prompt or PowerShell as Administrator"
    echo -e "3. Navigate to the directory containing the scripts and $TARFILE"
    echo -e "4. Run: ${BLUE}import-docker-image.bat${NC}"
    echo -e "5. Run: ${BLUE}start-docker.bat${NC}"
    echo ""
else
    echo -e "${RED}❌ Failed to export Docker image${NC}"
    echo "Please check the error messages above."
fi
