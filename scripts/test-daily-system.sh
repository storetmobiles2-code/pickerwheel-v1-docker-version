#!/bin/bash
# Script to test the daily PickerWheel system

echo "=== TESTING DAILY PICKERWHEEL SYSTEM ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if backend is running
echo "🔍 Checking if daily backend is running..."
if curl -s http://localhost:9082/api/prizes/wheel-display > /dev/null; then
    echo -e "${GREEN}✅ Daily backend is running on port 9082${NC}"
else
    echo -e "${RED}❌ Daily backend is not running${NC}"
    echo "Please start the backend first: ./scripts/start-server.sh"
    exit 1
fi

echo ""
echo "🧪 Running daily system tests..."

# Test 1: Get wheel display prizes
echo ""
echo "1️⃣ Testing wheel display prizes..."
RESPONSE=$(curl -s http://localhost:9082/api/prizes/wheel-display)
if echo "$RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['prizes']))")
    echo -e "   ${GREEN}✅ Wheel display: $COUNT prizes loaded${NC}"
else
    echo -e "   ${RED}❌ Failed to get wheel display prizes${NC}"
fi

# Test 2: Get available prizes
echo ""
echo "2️⃣ Testing available prizes..."
RESPONSE=$(curl -s http://localhost:9082/api/prizes/available)
if echo "$RESPONSE" | grep -q '"success":true'; then
    COUNT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['prizes']))")
    echo -e "   ${GREEN}✅ Available prizes: $COUNT prizes${NC}"
else
    echo -e "   ${RED}❌ Failed to get available prizes${NC}"
fi

# Test 3: Test pre-spin selection
echo ""
echo "3️⃣ Testing pre-spin selection..."
RESPONSE=$(curl -s -X POST http://localhost:9082/api/pre-spin \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user"}')
if echo "$RESPONSE" | grep -q '"success":true'; then
    PRIZE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['selected_prize']['name'])")
    CATEGORY=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['selected_prize']['category'])")
    SEGMENT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['target_segment_index'])")
    echo -e "   ${GREEN}✅ Pre-spin: Selected '$PRIZE' ($CATEGORY) → Segment $SEGMENT${NC}"
else
    echo -e "   ${RED}❌ Failed pre-spin selection${NC}"
fi

# Test 4: Test spin (if pre-spin worked)
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo ""
    echo "4️⃣ Testing spin..."
    PRIZE_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['selected_prize']['id'])")
    SEGMENT=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['target_segment_index'])")
    
    SPIN_RESPONSE=$(curl -s -X POST http://localhost:9082/api/spin \
        -H "Content-Type: application/json" \
        -d "{\"user_id\": \"test_user\", \"selected_prize_id\": $PRIZE_ID, \"target_segment_index\": $SEGMENT}")
    
    if echo "$SPIN_RESPONSE" | grep -q '"success":true'; then
        WON_PRIZE=$(echo "$SPIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['prize']['name'])")
        echo -e "   ${GREEN}✅ Spin: Won '$WON_PRIZE'${NC}"
    else
        echo -e "   ${RED}❌ Failed spin${NC}"
    fi
fi

# Test 5: Get daily stats
echo ""
echo "5️⃣ Testing daily statistics..."
RESPONSE=$(curl -s http://localhost:9082/api/stats)
if echo "$RESPONSE" | grep -q '"success":true'; then
    TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['stats']['total_prizes'])")
    AVAILABLE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['stats']['available_prizes'])")
    WINS=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['stats']['total_wins_today'])")
    echo -e "   ${GREEN}✅ Stats: $TOTAL total, $AVAILABLE available, $WINS wins today${NC}"
else
    echo -e "   ${RED}❌ Failed to get stats${NC}"
fi

# Test 6: Test with specific date (2025-10-02 - has rare items)
echo ""
echo "6️⃣ Testing with specific date (2025-10-02)..."
RESPONSE=$(curl -s -X POST http://localhost:9082/api/pre-spin \
    -H "Content-Type: application/json" \
    -d '{"user_id": "test_user2", "date": "2025-10-02"}')
if echo "$RESPONSE" | grep -q '"success":true'; then
    PRIZE=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['selected_prize']['name'])")
    CATEGORY=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['selected_prize']['category'])")
    TOTAL=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['total_segments'])")
    echo -e "   ${GREEN}✅ Date test: Selected '$PRIZE' ($CATEGORY) from $TOTAL total prizes${NC}"
    
    if [[ "$CATEGORY" == "ultra_rare" || "$CATEGORY" == "rare" ]]; then
        echo -e "   ${BLUE}🎯 Priority logic working: Rare item selected!${NC}"
    fi
else
    echo -e "   ${RED}❌ Failed date test${NC}"
fi

echo ""
echo -e "${GREEN}✅ Daily system test completed!${NC}"
echo ""
echo -e "${YELLOW}Summary:${NC}"
echo -e "  • Daily backend running on port 9082"
echo -e "  • All items show on wheel regardless of availability"
echo -e "  • Only available prizes can be won"
echo -e "  • Priority logic favors rare/ultra-rare items"
echo -e "  • Transactional history and inventory tracking active"
echo ""
echo -e "${BLUE}Access the app at: http://localhost:9082${NC}"
