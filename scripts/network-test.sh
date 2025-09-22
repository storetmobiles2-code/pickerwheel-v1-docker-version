#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== PICKERWHEEL NETWORK TEST ===${NC}"
echo ""

# Get the host IP address
HOST_IP=$(hostname -I 2>/dev/null || ifconfig | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1)
if [[ -z "$HOST_IP" ]]; then
    HOST_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "Could not determine IP")
fi

echo -e "${BLUE}Your IP address:${NC} $HOST_IP"
echo ""

# Check if the port is open
echo -e "${YELLOW}Testing if port 9080 is accessible...${NC}"
nc -z -v -w5 localhost 9080 2>&1 || echo -e "${RED}Port 9080 is not accessible on localhost${NC}"
echo ""

# Check if Docker container is running
echo -e "${YELLOW}Docker container status:${NC}"
docker-compose ps
echo ""

# Try to access the application
echo -e "${YELLOW}Testing HTTP connection to application...${NC}"
curl -s -o /dev/null -w "%{http_code}" http://localhost:9080 || echo -e "${RED}Failed to connect to application${NC}"
echo ""

# Provide QR code for mobile access
echo -e "${YELLOW}Scan this QR code with your mobile device to access the application:${NC}"
echo "http://$HOST_IP:9080" | qrencode -t ANSIUTF8 2>/dev/null || echo -e "${RED}QR code generation failed. Install qrencode with: brew install qrencode${NC}"
echo ""

echo -e "${YELLOW}If your mobile device cannot connect, try these troubleshooting steps:${NC}"
echo "1. Make sure your mobile device is on the same WiFi network"
echo "2. Check if your computer's firewall is blocking incoming connections"
echo "3. Try accessing http://$HOST_IP:9080 directly on your mobile browser"
echo "4. Restart your router if network issues persist"
echo ""
