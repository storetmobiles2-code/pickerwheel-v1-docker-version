#!/bin/bash
# System Status Script for Daily PickerWheel

echo "=== DAILY PICKERWHEEL SYSTEM STATUS ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo "🔍 Checking system status..."
echo ""

# 1. Check if backend is running
echo "1️⃣ Backend Status:"
if curl -s http://localhost:9082/api/prizes/wheel-display > /dev/null; then
    echo -e "   ${GREEN}✅ Daily backend is running on port 9082${NC}"
    
    # Get total items
    TOTAL_ITEMS=$(curl -s http://localhost:9082/api/prizes/wheel-display | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total_items'])" 2>/dev/null || echo "Unknown")
    echo -e "   ${BLUE}📊 Total items on wheel: $TOTAL_ITEMS${NC}"
else
    echo -e "   ${RED}❌ Daily backend is not running${NC}"
    echo -e "   ${YELLOW}💡 Start with: ./scripts/start-server.sh${NC}"
fi

# 2. Check itemlist file
echo ""
echo "2️⃣ Item List Status:"
if [ -f "itemlist_dates.txt" ]; then
    ITEM_COUNT=$(grep -v '^#' itemlist_dates.txt | grep -v '^$' | grep -v '^Item,' | wc -l)
    echo -e "   ${GREEN}✅ itemlist_dates.txt found${NC}"
    echo -e "   ${BLUE}📋 Items defined: $ITEM_COUNT${NC}"
    
    # Show categories
    echo "   Categories:"
    COMMON=$(grep -i 'common' itemlist_dates.txt | wc -l)
    RARE=$(grep -i 'rare' itemlist_dates.txt | wc -l)
    ULTRA_RARE=$(grep -i 'ultra rare' itemlist_dates.txt | wc -l)
    echo -e "     ${BLUE}• Common: $COMMON${NC}"
    echo -e "     ${BLUE}• Rare: $RARE${NC}"
    echo -e "     ${BLUE}• Ultra Rare: $ULTRA_RARE${NC}"
else
    echo -e "   ${RED}❌ itemlist_dates.txt not found${NC}"
fi

# 3. Check daily CSV files
echo ""
echo "3️⃣ Daily CSV Files:"
if [ -d "daily_csvs" ]; then
    CSV_COUNT=$(ls daily_csvs/prizes_*.csv 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ Daily CSV directory exists${NC}"
    echo -e "   ${BLUE}📁 CSV files: $CSV_COUNT${NC}"
    
    if [ $CSV_COUNT -gt 0 ]; then
        FIRST_DATE=$(ls daily_csvs/prizes_*.csv | head -1 | sed 's/.*prizes_\(.*\)\.csv/\1/')
        LAST_DATE=$(ls daily_csvs/prizes_*.csv | tail -1 | sed 's/.*prizes_\(.*\)\.csv/\1/')
        echo -e "   ${BLUE}📅 Date range: $FIRST_DATE to $LAST_DATE${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠️  Daily CSV directory not found${NC}"
    echo -e "   ${YELLOW}💡 Generate with: python3 scripts/generate_daily_csv.py${NC}"
fi

# 4. Check database
echo ""
echo "4️⃣ Database Status:"
if [ -f "pickerwheel_contest.db" ]; then
    echo -e "   ${GREEN}✅ Database file exists${NC}"
    DB_SIZE=$(du -h pickerwheel_contest.db | cut -f1)
    echo -e "   ${BLUE}💾 Size: $DB_SIZE${NC}"
else
    echo -e "   ${YELLOW}⚠️  Database file not found (will be created on first run)${NC}"
fi

# 5. System configuration
echo ""
echo "5️⃣ System Configuration:"
echo -e "   ${BLUE}🌐 Port: 9082${NC}"
echo -e "   ${BLUE}📂 Backend: daily_database_backend.py${NC}"
echo -e "   ${BLUE}🎯 Mode: Daily items with transactional history${NC}"
echo -e "   ${BLUE}📋 Source: itemlist_dates.txt${NC}"

# 6. Quick test
echo ""
echo "6️⃣ Quick System Test:"
if curl -s http://localhost:9082/api/prizes/wheel-display > /dev/null; then
    # Test wheel display
    WHEEL_ITEMS=$(curl -s http://localhost:9082/api/prizes/wheel-display | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['prizes']))" 2>/dev/null || echo "0")
    
    # Test available prizes
    AVAILABLE_ITEMS=$(curl -s http://localhost:9082/api/prizes/available | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['prizes']))" 2>/dev/null || echo "0")
    
    echo -e "   ${GREEN}✅ Wheel display: $WHEEL_ITEMS items${NC}"
    echo -e "   ${GREEN}✅ Available today: $AVAILABLE_ITEMS items${NC}"
    
    if [ "$WHEEL_ITEMS" -gt "$AVAILABLE_ITEMS" ]; then
        echo -e "   ${BLUE}🎯 System working correctly: Shows all items, awards only available ones${NC}"
    fi
else
    echo -e "   ${RED}❌ Backend not responding${NC}"
fi

echo ""
echo "=== SUMMARY ==="
echo ""
echo -e "${GREEN}✅ System Features:${NC}"
echo -e "  • Always shows ALL items from itemlist_dates.txt on wheel"
echo -e "  • Only awards items available for the current date"
echo -e "  • Respects daily limits (e.g., 1 ultra-rare item per day)"
echo -e "  • Maintains complete transactional history"
echo -e "  • Priority logic favors rare/ultra-rare items when available"
echo ""
echo -e "${BLUE}🔧 Management Commands:${NC}"
echo -e "  • Start system: ./scripts/start-server.sh"
echo -e "  • Stop system: ./scripts/stop-server.sh"
echo -e "  • Test system: ./scripts/test-daily-system.sh"
echo -e "  • Manage items: python3 scripts/manage-itemlist.py list"
echo -e "  • Manage CSVs: ./scripts/manage-daily-csvs.sh status"
echo ""
echo -e "${YELLOW}📝 To update items:${NC}"
echo -e "  • Edit itemlist_dates.txt directly"
echo -e "  • Or use: python3 scripts/manage-itemlist.py add 'New Item' 'Common' '50' '10' '*'"
echo ""
echo -e "${BLUE}🌐 Access: http://localhost:9082${NC}"
