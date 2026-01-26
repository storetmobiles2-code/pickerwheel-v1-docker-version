#!/bin/bash
# PickerWheel Docker Management Script
# Supports both legacy (SQLite) and new (PostgreSQL) backends

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Script configuration - NEW PostgreSQL backend
PORT="9080"
COMPOSE_FILE="docker-compose.yml"
CONTAINER_PREFIX="pickerwheel"

# Legacy configuration
LEGACY_PORT="8082"
LEGACY_COMPOSE_FILE="docker-compose.yml"

# Detect which mode we're in
CURRENT_MODE="new"  # Default to new PostgreSQL mode

# Function to get container name dynamically
get_container_name() {
    docker ps -a --format "{{.Names}}" | grep "$CONTAINER_PREFIX" | head -1
}

# Function to get PostgreSQL container name
get_db_container() {
    docker ps -a --format "{{.Names}}" | grep "pickerwheel-db" | head -1
}

# Function to show usage
show_usage() {
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║      ${YELLOW}PICKERWHEEL DOCKER MANAGEMENT v2.0${MAGENTA}                 ║${NC}"
    echo -e "${MAGENTA}║      ${CYAN}PostgreSQL Backend with Real-Time Updates${MAGENTA}          ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  start       - Start PostgreSQL + PickerWheel containers"
    echo "  stop        - Stop all containers"
    echo "  restart     - Restart all containers"
    echo "  status      - Show container status"
    echo "  logs        - Show container logs"
    echo "  db-logs     - Show PostgreSQL logs"
    echo "  migrate     - Run data migration from itemlist_dates_v2.txt"
    echo "  shell       - Open shell in app container"
    echo "  db-shell    - Open PostgreSQL shell"
    echo "  info        - Show system information"
    echo "  test        - Test the running system"
    echo "  clean       - Clean up Docker resources"
    echo "  legacy      - Use legacy SQLite backend"
    echo "  help        - Show this help message"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo "  $0 start                    # Start PostgreSQL backend"
    echo "  $0 migrate                  # Run data migration"
    echo "  $0 logs                     # View app logs"
    echo "  $0 db-shell                 # Access PostgreSQL"
    echo "  $0 legacy start             # Use legacy SQLite backend"
    echo ""
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        echo "Please install Docker from https://www.docker.com/products/docker-desktop"
        exit 1
    fi

    # Check for docker compose (v2) or docker-compose (v1)
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        echo -e "${RED}Error: Docker Compose is not available${NC}"
        echo "Please install Docker Compose"
        exit 1
    fi
}

# Function to get host IP
get_host_ip() {
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

# Function to start Docker containers
start_container() {
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║        ${GREEN}STARTING PICKERWHEEL (PostgreSQL)${MAGENTA}                 ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    check_docker
    
    # Check if already running
    if docker ps | grep -q "$CONTAINER_PREFIX"; then
        echo -e "${YELLOW}⚠️  Containers are already running${NC}"
        echo "Use '$0 restart' to restart, or '$0 stop' to stop first"
        return 1
    fi
    
    echo -e "${YELLOW}📦 Building and starting containers...${NC}"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Containers started successfully!${NC}"
        echo ""
        
        # Wait for PostgreSQL to be ready
        echo -e "${YELLOW}⏳ Waiting for PostgreSQL to be ready...${NC}"
        sleep 5
        
        # Check if database is ready
        for i in {1..30}; do
            if docker exec pickerwheel-db pg_isready -U pickerwheel -d pickerwheel &>/dev/null; then
                echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
                break
            fi
            sleep 1
        done
        
        echo ""
        show_access_info
    else
        echo -e "${RED}❌ Failed to start containers${NC}"
        echo "Check the error messages above."
        return 1
    fi
}

# Function to stop Docker containers
stop_container() {
    echo -e "${YELLOW}=== STOPPING PICKERWHEEL CONTAINERS ===${NC}"
    echo ""
    
    check_docker
    
    if ! docker ps | grep -q "$CONTAINER_PREFIX"; then
        echo -e "${YELLOW}⚠️  Containers are not running${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}Stopping containers...${NC}"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Containers stopped successfully!${NC}"
    else
        echo -e "${RED}❌ Failed to stop containers${NC}"
        return 1
    fi
}

# Function to restart Docker containers
restart_container() {
    echo -e "${YELLOW}=== RESTARTING PICKERWHEEL CONTAINERS ===${NC}"
    echo ""
    
    check_docker
    
    echo -e "${YELLOW}Stopping containers...${NC}"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
    
    sleep 3
    
    echo -e "${YELLOW}Starting containers...${NC}"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Containers restarted successfully!${NC}"
        echo ""
        
        # Wait for PostgreSQL
        echo -e "${YELLOW}⏳ Waiting for PostgreSQL...${NC}"
        sleep 5
        
        show_access_info
    else
        echo -e "${RED}❌ Failed to restart containers${NC}"
        return 1
    fi
}

# Function to show container status
show_status() {
    echo -e "${YELLOW}=== CONTAINER STATUS ===${NC}"
    echo ""
    
    check_docker
    
    # Show all pickerwheel containers
    echo -e "${CYAN}Containers:${NC}"
    docker ps -a --filter "name=$CONTAINER_PREFIX" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Check if app is responding
    if docker ps | grep -q "pickerwheel-app"; then
        echo -e "${CYAN}Application Health:${NC}"
        if curl -s "http://localhost:$PORT/api/health" > /dev/null 2>&1; then
            HEALTH=$(curl -s "http://localhost:$PORT/api/health" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Status: {d.get('status', 'unknown')}\")" 2>/dev/null)
            echo -e "${GREEN}✅ $HEALTH${NC}"
        else
            echo -e "${YELLOW}⏳ Application starting up...${NC}"
        fi
    else
        echo -e "${RED}❌ App container not running${NC}"
    fi
    
    # Check PostgreSQL
    if docker ps | grep -q "pickerwheel-db"; then
        echo ""
        echo -e "${CYAN}Database Health:${NC}"
        if docker exec pickerwheel-db pg_isready -U pickerwheel -d pickerwheel &>/dev/null; then
            echo -e "${GREEN}✅ PostgreSQL is ready${NC}"
            
            # Get prize count
            PRIZE_COUNT=$(docker exec pickerwheel-db psql -U pickerwheel -d pickerwheel -t -c "SELECT COUNT(*) FROM prizes WHERE is_active = TRUE;" 2>/dev/null | tr -d ' ')
            if [ ! -z "$PRIZE_COUNT" ] && [ "$PRIZE_COUNT" != "" ]; then
                echo -e "${BLUE}📊 Active prizes: $PRIZE_COUNT${NC}"
            fi
        else
            echo -e "${YELLOW}⏳ PostgreSQL starting...${NC}"
        fi
    else
        echo -e "${RED}❌ Database container not running${NC}"
    fi
}

# Function to show app logs
show_logs() {
    echo -e "${YELLOW}=== APPLICATION LOGS ===${NC}"
    echo ""
    
    check_docker
    
    if docker ps | grep -q "pickerwheel-app"; then
        echo -e "${CYAN}Showing recent logs (Ctrl+C to exit):${NC}"
        echo ""
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs -f --tail=50 pickerwheel
    else
        echo -e "${YELLOW}⚠️  App container is not running${NC}"
    fi
}

# Function to show database logs
show_db_logs() {
    echo -e "${YELLOW}=== POSTGRESQL LOGS ===${NC}"
    echo ""
    
    check_docker
    
    if docker ps | grep -q "pickerwheel-db"; then
        echo -e "${CYAN}Showing recent logs (Ctrl+C to exit):${NC}"
        echo ""
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs -f --tail=50 postgres
    else
        echo -e "${YELLOW}⚠️  Database container is not running${NC}"
    fi
}

# Function to run data migration
run_migration() {
    echo -e "${YELLOW}=== RUNNING DATA MIGRATION ===${NC}"
    echo ""
    
    check_docker
    
    if ! docker ps | grep -q "pickerwheel-app"; then
        echo -e "${RED}❌ App container is not running${NC}"
        echo "Start containers first with: $0 start"
        return 1
    fi
    
    echo -e "${CYAN}Running migration script...${NC}"
    docker exec -it pickerwheel-app python /app/backend/scripts/migrate_data.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Migration completed!${NC}"
    else
        echo -e "${RED}❌ Migration failed${NC}"
        return 1
    fi
}

# Function to open app shell
open_shell() {
    echo -e "${YELLOW}=== OPENING APP SHELL ===${NC}"
    echo ""
    
    check_docker
    
    if ! docker ps | grep -q "pickerwheel-app"; then
        echo -e "${RED}❌ App container is not running${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Connecting to app container...${NC}"
    echo -e "${YELLOW}Type 'exit' to return${NC}"
    echo ""
    docker exec -it pickerwheel-app /bin/bash
}

# Function to open database shell
open_db_shell() {
    echo -e "${YELLOW}=== OPENING POSTGRESQL SHELL ===${NC}"
    echo ""
    
    check_docker
    
    if ! docker ps | grep -q "pickerwheel-db"; then
        echo -e "${RED}❌ Database container is not running${NC}"
        return 1
    fi
    
    echo -e "${CYAN}Connecting to PostgreSQL...${NC}"
    echo -e "${YELLOW}Type '\\q' to exit${NC}"
    echo ""
    docker exec -it pickerwheel-db psql -U pickerwheel -d pickerwheel
}

# Function to show system information
show_info() {
    echo -e "${YELLOW}=== SYSTEM INFORMATION ===${NC}"
    echo ""
    
    check_docker
    
    # Docker version
    echo -e "${CYAN}Docker Version:${NC}"
    docker --version
    $DOCKER_COMPOSE version 2>/dev/null || docker-compose --version 2>/dev/null
    echo ""
    
    # Containers
    echo -e "${CYAN}Container Status:${NC}"
    docker ps -a --filter "name=$CONTAINER_PREFIX" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Network
    HOST_IP=$(get_host_ip)
    echo -e "${CYAN}Network Access:${NC}"
    echo "Local:   http://localhost:$PORT"
    echo "Network: http://$HOST_IP:$PORT"
    echo ""
    
    # Database info
    if docker ps | grep -q "pickerwheel-db"; then
        echo -e "${CYAN}Database Info:${NC}"
        docker exec pickerwheel-db psql -U pickerwheel -d pickerwheel -c "SELECT COUNT(*) as prizes FROM prizes WHERE is_active = TRUE; SELECT COUNT(*) as transactions FROM transactions;" 2>/dev/null || echo "Database not ready"
    fi
    echo ""
    
    show_access_info
}

# Function to test the system
test_system() {
    echo -e "${YELLOW}=== TESTING PICKERWHEEL SYSTEM ===${NC}"
    echo ""
    
    check_docker
    
    if ! docker ps | grep -q "pickerwheel-app"; then
        echo -e "${RED}❌ App container is not running${NC}"
        echo "Start containers first with: $0 start"
        return 1
    fi
    
    echo -e "${CYAN}Testing API endpoints...${NC}"
    echo ""
    
    # Test health
    echo "1️⃣  Health check..."
    if curl -s "http://localhost:$PORT/api/health" > /dev/null; then
        echo -e "   ${GREEN}✅ Health endpoint OK${NC}"
    else
        echo -e "   ${RED}❌ Health endpoint failed${NC}"
    fi
    
    # Test wheel display
    echo "2️⃣  Wheel display..."
    RESULT=$(curl -s "http://localhost:$PORT/api/prizes/wheel-display" 2>/dev/null)
    if echo "$RESULT" | grep -q "success"; then
        TOTAL=$(echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('total_items', 0))" 2>/dev/null)
        echo -e "   ${GREEN}✅ Wheel display OK ($TOTAL items)${NC}"
    else
        echo -e "   ${RED}❌ Wheel display failed${NC}"
    fi
    
    # Test available prizes
    echo "3️⃣  Available prizes..."
    RESULT=$(curl -s "http://localhost:$PORT/api/prizes/available" 2>/dev/null)
    if echo "$RESULT" | grep -q "success"; then
        COUNT=$(echo "$RESULT" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('available_count', 0))" 2>/dev/null)
        echo -e "   ${GREEN}✅ Available prizes OK ($COUNT available)${NC}"
    else
        echo -e "   ${RED}❌ Available prizes failed${NC}"
    fi
    
    # Test stats
    echo "4️⃣  Statistics..."
    if curl -s "http://localhost:$PORT/api/stats" | grep -q "success"; then
        echo -e "   ${GREEN}✅ Statistics OK${NC}"
    else
        echo -e "   ${RED}❌ Statistics failed${NC}"
    fi
    
    # Test categories
    echo "5️⃣  Categories..."
    if curl -s "http://localhost:$PORT/api/categories" | grep -q "success"; then
        echo -e "   ${GREEN}✅ Categories OK${NC}"
    else
        echo -e "   ${RED}❌ Categories failed${NC}"
    fi
    
    echo ""
    echo -e "${GREEN}✅ System test completed!${NC}"
}

# Function to clean up Docker resources
clean_docker() {
    echo -e "${YELLOW}=== CLEANING DOCKER RESOURCES ===${NC}"
    echo ""
    
    check_docker
    
    echo -e "${RED}⚠️  This will remove all PickerWheel containers and volumes!${NC}"
    read -p "Are you sure? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}Stopping containers...${NC}"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" down -v
        
        echo -e "${YELLOW}Removing unused images...${NC}"
        docker image prune -f
        
        echo -e "${YELLOW}Removing unused volumes...${NC}"
        docker volume prune -f
        
        echo ""
        echo -e "${GREEN}✅ Cleanup completed!${NC}"
    else
        echo "Cancelled."
    fi
}

# Function to show access information
show_access_info() {
    HOST_IP=$(get_host_ip)
    
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║                    ${GREEN}ACCESS INFORMATION${MAGENTA}                    ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}🌐 Local Access:${NC}"
    echo -e "   Main Wheel:     ${BLUE}http://localhost:$PORT${NC}"
    echo -e "   Admin Panel:    ${BLUE}http://localhost:$PORT/admin${NC}"
    echo ""
    echo -e "${GREEN}📡 Network Access:${NC}"
    echo -e "   Main Wheel:     ${BLUE}http://$HOST_IP:$PORT${NC}"
    echo -e "   Admin Panel:    ${BLUE}http://$HOST_IP:$PORT/admin${NC}"
    echo ""
    echo -e "${GREEN}🔐 Admin Credentials:${NC}"
    echo -e "   Password: ${YELLOW}myTAdmin2025${NC}"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo -e "   Stop:     ${BLUE}$0 stop${NC}"
    echo -e "   Logs:     ${BLUE}$0 logs${NC}"
    echo -e "   Status:   ${BLUE}$0 status${NC}"
    echo -e "   Migrate:  ${BLUE}$0 migrate${NC}"
    echo ""
}

# Function to run legacy mode
run_legacy() {
    COMPOSE_FILE="$LEGACY_COMPOSE_FILE"
    PORT="$LEGACY_PORT"
    echo -e "${YELLOW}⚠️  Using legacy SQLite backend${NC}"
    echo ""
    
    shift  # Remove 'legacy' from args
    
    case "${1:-help}" in
        start)
            echo -e "${YELLOW}Starting legacy backend...${NC}"
            check_docker
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d --build
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✅ Legacy backend started!${NC}"
                echo "Access: http://localhost:$PORT"
            fi
            ;;
        stop)
            check_docker
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
            ;;
        *)
            echo "Legacy mode: $0 legacy [start|stop]"
            ;;
    esac
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
    db-logs)
        show_db_logs
        ;;
    migrate)
        run_migration
        ;;
    shell)
        open_shell
        ;;
    db-shell)
        open_db_shell
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
    legacy)
        run_legacy "$@"
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
