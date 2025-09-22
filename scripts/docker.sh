#!/bin/bash
# Comprehensive Docker Management Script for Daily PickerWheel System

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script configuration
PORT="8082"
BACKEND_PORT="9082"

# Function to get container name dynamically
get_container_name() {
    docker ps -a --format "table {{.Names}}" | grep "pickerwheel-v1-docker-version" | head -1
}

# Function to show usage
show_usage() {
    echo -e "${YELLOW}=== DAILY PICKERWHEEL DOCKER MANAGEMENT ===${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  start       - Build and start Docker container"
    echo "  stop        - Stop and remove Docker container"
    echo "  restart     - Restart Docker container"
    echo "  status      - Show container status"
    echo "  logs        - Show container logs"
    echo "  info        - Show system information"
    echo "  test        - Test the running system"
    echo "  clean       - Clean up Docker resources"
    echo "  help        - Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  $0 start                    # Start the container"
    echo "  $0 stop                     # Stop the container"
    echo "  $0 restart                  # Restart the container"
    echo "  $0 status                   # Check container status"
    echo "  $0 logs                     # View container logs"
    echo "  $0 info                     # Show system information"
    echo "  $0 test                     # Test the system"
    echo "  $0 clean                    # Clean up Docker resources"
    echo ""
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        echo "Please install Docker from https://www.docker.com/products/docker-desktop"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
}

# Function to get host IP
get_host_ip() {
    # Try different methods to get host IP
    HOST_IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v "127.0.0.1" | awk '{print $2}' | head -n 1)
    if [[ -z "$HOST_IP" ]]; then
        HOST_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
    fi
    if [[ -z "$HOST_IP" ]]; then
        HOST_IP=$(ip route get 1 2>/dev/null | awk '{print $7}' | head -n 1)
    fi
    if [[ -z "$HOST_IP" ]]; then
        HOST_IP="<your-ip-address>"
    fi
    echo "$HOST_IP"
}

# Function to start Docker container
start_container() {
    echo -e "${YELLOW}=== STARTING PICKERWHEEL DOCKER CONTAINER ===${NC}"
    echo ""
    
    check_docker
    
    # Check if container is already running
    CONTAINER_NAME=$(get_container_name)
    if [ ! -z "$CONTAINER_NAME" ] && docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${YELLOW}⚠️  Container is already running${NC}"
        echo "Use '$0 restart' to restart it, or '$0 stop' to stop it first"
        return 1
    fi
    
    echo -e "${YELLOW}Building and starting Docker container...${NC}"
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PickerWheel Docker container started successfully!${NC}"
        echo ""
        show_access_info
    else
        echo -e "${RED}❌ Failed to start PickerWheel Docker container${NC}"
        echo "Please check the error messages above."
        return 1
    fi
}

# Function to stop Docker container
stop_container() {
    echo -e "${YELLOW}=== STOPPING PICKERWHEEL DOCKER CONTAINER ===${NC}"
    echo ""
    
    check_docker
    
    CONTAINER_NAME=$(get_container_name)
    if [ -z "$CONTAINER_NAME" ] || ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${YELLOW}⚠️  Container is not running${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Stopping and removing Docker container...${NC}"
    docker-compose down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PickerWheel Docker container stopped successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to stop PickerWheel Docker container${NC}"
        return 1
    fi
}

# Function to restart Docker container
restart_container() {
    echo -e "${YELLOW}=== RESTARTING PICKERWHEEL DOCKER CONTAINER ===${NC}"
    echo ""
    
    check_docker
    
    # Force stop and remove container
    echo -e "${YELLOW}Stopping and removing existing container...${NC}"
    docker-compose down
    
    # Wait a moment for cleanup
    sleep 3
    
    # Start fresh
    echo -e "${YELLOW}Starting fresh container...${NC}"
    docker-compose up -d --build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ PickerWheel Docker container restarted successfully!${NC}"
        echo ""
        show_access_info
    else
        echo -e "${RED}❌ Failed to restart PickerWheel Docker container${NC}"
        echo "Please check the error messages above."
        return 1
    fi
}

# Function to show container status
show_status() {
    echo -e "${YELLOW}=== DOCKER CONTAINER STATUS ===${NC}"
    echo ""
    
    check_docker
    
    # Check if container exists
    CONTAINER_NAME=$(get_container_name)
    if [ ! -z "$CONTAINER_NAME" ] && docker ps -a | grep -q "$CONTAINER_NAME"; then
        echo -e "${CYAN}Container Status:${NC}"
        docker ps -a | grep "$CONTAINER_NAME"
        echo ""
        
        # Check if container is running
        if docker ps | grep -q "$CONTAINER_NAME"; then
            echo -e "${GREEN}✅ Container is running${NC}"
            echo ""
            
            # Test if the application is responding
            echo -e "${CYAN}Application Status:${NC}"
            if curl -s http://localhost:$PORT/api/prizes/wheel-display > /dev/null; then
                echo -e "${GREEN}✅ Application is responding on port $PORT${NC}"
                
                # Get total items
                TOTAL_ITEMS=$(curl -s http://localhost:$PORT/api/prizes/wheel-display | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total_items'])" 2>/dev/null || echo "Unknown")
                echo -e "${BLUE}📊 Total items on wheel: $TOTAL_ITEMS${NC}"
            else
                echo -e "${RED}❌ Application is not responding${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  Container is stopped${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Container does not exist${NC}"
        echo "Use '$0 start' to create and start the container"
    fi
}

# Function to show container logs
show_logs() {
    echo -e "${YELLOW}=== DOCKER CONTAINER LOGS ===${NC}"
    echo ""
    
    check_docker
    
    CONTAINER_NAME=$(get_container_name)
    if [ ! -z "$CONTAINER_NAME" ] && docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${CYAN}Showing recent logs (last 50 lines):${NC}"
        echo ""
        docker-compose logs --tail=50 -f
    else
        echo -e "${YELLOW}⚠️  Container is not running${NC}"
        echo "Use '$0 start' to start the container first"
    fi
}

# Function to show system information
show_info() {
    echo -e "${YELLOW}=== SYSTEM INFORMATION ===${NC}"
    echo ""
    
    check_docker
    
    # Docker version
    echo -e "${CYAN}Docker Version:${NC}"
    docker --version
    docker-compose --version
    echo ""
    
    # Container information
    echo -e "${CYAN}Container Information:${NC}"
    CONTAINER_NAME=$(get_container_name)
    if [ ! -z "$CONTAINER_NAME" ] && docker ps -a | grep -q "$CONTAINER_NAME"; then
        docker inspect "$CONTAINER_NAME" --format='{{.Name}}: {{.State.Status}} ({{.State.StartedAt}})'
    else
        echo "Container does not exist"
    fi
    echo ""
    
    # Port information
    echo -e "${CYAN}Port Information:${NC}"
    echo "External Port: $PORT"
    echo "Internal Port: $BACKEND_PORT"
    echo ""
    
    # Network information
    HOST_IP=$(get_host_ip)
    echo -e "${CYAN}Network Access:${NC}"
    echo "Local:  http://localhost:$PORT"
    echo "Network: http://$HOST_IP:$PORT"
    echo ""
    
    # File system information
    echo -e "${CYAN}File System:${NC}"
    if [ -f "itemlist_dates.txt" ]; then
        ITEM_COUNT=$(grep -v '^#' itemlist_dates.txt | grep -v '^$' | grep -v '^Item,' | wc -l)
        echo "✅ itemlist_dates.txt found ($ITEM_COUNT items)"
    else
        echo "❌ itemlist_dates.txt not found"
    fi
    
    if [ -d "daily_csvs" ]; then
        CSV_COUNT=$(ls daily_csvs/prizes_*.csv 2>/dev/null | wc -l)
        echo "✅ Daily CSV directory found ($CSV_COUNT files)"
    else
        echo "❌ Daily CSV directory not found"
    fi
    
    if [ -f "pickerwheel_contest.db" ]; then
        DB_SIZE=$(du -h pickerwheel_contest.db | cut -f1)
        echo "✅ Database found ($DB_SIZE)"
    else
        echo "❌ Database not found"
    fi
    echo ""
    
    # Access information
    show_access_info
}

# Function to test the system
test_system() {
    echo -e "${YELLOW}=== TESTING PICKERWHEEL SYSTEM ===${NC}"
    echo ""
    
    # Check if container is running
    CONTAINER_NAME=$(get_container_name)
    if [ -z "$CONTAINER_NAME" ] || ! docker ps | grep -q "$CONTAINER_NAME"; then
        echo -e "${RED}❌ Container is not running${NC}"
        echo "Use '$0 start' to start the container first"
        return 1
    fi
    
    # Test API endpoints
    echo -e "${CYAN}Testing API endpoints...${NC}"
    
    # Test wheel display
    echo "1️⃣ Testing wheel display..."
    if curl -s http://localhost:$PORT/api/prizes/wheel-display > /dev/null; then
        TOTAL_ITEMS=$(curl -s http://localhost:$PORT/api/prizes/wheel-display | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total_items'])" 2>/dev/null || echo "Unknown")
        echo -e "   ${GREEN}✅ Wheel display: $TOTAL_ITEMS items${NC}"
    else
        echo -e "   ${RED}❌ Wheel display failed${NC}"
    fi
    
    # Test available prizes
    echo "2️⃣ Testing available prizes..."
    if curl -s http://localhost:$PORT/api/prizes/available > /dev/null; then
        AVAILABLE_ITEMS=$(curl -s http://localhost:$PORT/api/prizes/available | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['prizes']))" 2>/dev/null || echo "Unknown")
        echo -e "   ${GREEN}✅ Available prizes: $AVAILABLE_ITEMS items${NC}"
    else
        echo -e "   ${RED}❌ Available prizes failed${NC}"
    fi
    
    # Test stats
    echo "3️⃣ Testing daily stats..."
    if curl -s http://localhost:$PORT/api/stats > /dev/null; then
        echo -e "   ${GREEN}✅ Daily stats working${NC}"
    else
        echo -e "   ${RED}❌ Daily stats failed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ System test completed!${NC}"
}

# Function to clean up Docker resources
clean_docker() {
    echo -e "${YELLOW}=== CLEANING UP DOCKER RESOURCES ===${NC}"
    echo ""
    
    check_docker
    
    echo -e "${YELLOW}Stopping and removing containers...${NC}"
    docker-compose down
    
    echo -e "${YELLOW}Removing unused images...${NC}"
    docker image prune -f
    
    echo -e "${YELLOW}Removing unused volumes...${NC}"
    docker volume prune -f
    
    echo -e "${YELLOW}Removing unused networks...${NC}"
    docker network prune -f
    
    echo -e "${GREEN}✅ Docker cleanup completed!${NC}"
}

# Function to show access information
show_access_info() {
    HOST_IP=$(get_host_ip)
    
    echo -e "${YELLOW}=== ACCESS INFORMATION ===${NC}"
    echo ""
    echo -e "${GREEN}Local Access:${NC}"
    echo -e "Main Contest:    ${BLUE}http://localhost:$PORT${NC}"
    echo -e "Admin Panel:     ${BLUE}http://localhost:$PORT/admin.html${NC}"
    echo ""
    echo -e "${GREEN}Network Access (for other devices):${NC}"
    echo -e "Main Contest:    ${BLUE}http://$HOST_IP:$PORT${NC}"
    echo -e "Admin Panel:     ${BLUE}http://$HOST_IP:$PORT/admin.html${NC}"
    echo ""
    echo -e "${YELLOW}Note:${NC} If you have a firewall enabled, make sure port $PORT is allowed."
    echo ""
    echo -e "${GREEN}Admin Credentials:${NC}"
    echo -e "Password: ${BLUE}myTAdmin2025${NC} (Use Ctrl+Alt+A to access admin panel)"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "Stop container:   ${BLUE}$0 stop${NC}"
    echo -e "View logs:        ${BLUE}$0 logs${NC}"
    echo -e "Check status:     ${BLUE}$0 status${NC}"
    echo -e "System info:      ${BLUE}$0 info${NC}"
    echo ""
}

# Main script logic
case "${1:-help}" in
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    info)
        show_info
        ;;
    test)
        test_system
        ;;
    clean)
        clean_docker
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
