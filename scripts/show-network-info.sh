#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== NETWORK INFORMATION FOR PICKERWHEEL ===${NC}"
echo ""

# Get operating system
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo -e "${BLUE}Operating System:${NC} $OS"
echo ""

# Get IP addresses
echo -e "${YELLOW}Available IP Addresses:${NC}"
echo ""

if [[ "$OS" == "macOS" ]]; then
    # macOS
    echo -e "${BLUE}Ethernet:${NC}"
    ipconfig getifaddr en0 2>/dev/null || echo "Not connected"
    
    echo -e "${BLUE}Wi-Fi:${NC}"
    ipconfig getifaddr en1 2>/dev/null || echo "Not connected"
    
elif [[ "$OS" == "Linux" ]]; then
    # Linux
    ip -4 addr | grep -v "127.0.0.1" | grep -v "docker" | grep "inet" | awk '{print $2}' | cut -d/ -f1
    
elif [[ "$OS" == "Windows" ]]; then
    # Windows (when running in Git Bash or similar)
    ipconfig | grep IPv4 | awk '{print $NF}'
    
else
    # Generic fallback
    hostname -I 2>/dev/null || echo "Could not determine IP address"
fi

echo ""
echo -e "${YELLOW}=== ACCESS INFORMATION ===${NC}"
echo ""

# Get the first non-localhost IP
IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if [[ -z "$IP" ]]; then
    # Try alternative methods
    IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1)
    if [[ -z "$IP" ]]; then
        IP="<your-ip-address>"
    fi
fi

echo -e "${GREEN}To access PickerWheel from other devices on your network:${NC}"
echo -e "Main Contest:    ${BLUE}http://$IP:8080${NC}"
echo -e "Admin Panel:     ${BLUE}http://$IP:8080/admin.html${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} If you have a firewall enabled, make sure port 8080 is allowed."
echo ""
