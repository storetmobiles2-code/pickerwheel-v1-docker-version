#!/bin/bash
# Script to verify daily limits for all rare and ultra-rare items

echo "=== VERIFYING DAILY LIMITS FOR RARE AND ULTRA-RARE ITEMS ==="
echo ""

# Configuration
ADMIN_PASSWORD="myTAdmin2025"
API_BASE_URL="http://localhost:9080/api"
TEST_DATE="2025-10-01"

# Reset inventory
echo "🔄 Resetting inventory..."
curl -s -X POST "$API_BASE_URL/admin/reset-inventory" \
  -H "Content-Type: application/json" \
  -d "{\"admin_password\": \"$ADMIN_PASSWORD\"}" > /dev/null
echo "Inventory reset"
echo ""

# Get all rare and ultra-rare prizes
echo "🔍 Getting all rare and ultra-rare prizes..."
cd ../backend
PRIZES=$(sqlite3 pickerwheel_contest.db "
  SELECT p.id, p.name, pc.name as category, pi.per_day_limit 
  FROM prizes p 
  JOIN prize_categories pc ON p.category_id = pc.id 
  JOIN prize_inventory pi ON p.id = pi.prize_id 
  WHERE (pc.name = 'rare' OR pc.name = 'ultra_rare') 
    AND pi.available_date = '$TEST_DATE' 
  ORDER BY pc.name, p.name;
")

if [ -z "$PRIZES" ]; then
  echo "No rare or ultra-rare prizes found for $TEST_DATE"
  exit 1
fi

# Test each prize
echo "🔄 Testing daily limits for each prize..."
echo ""

while IFS='|' read -r id name category limit; do
  echo "=== Testing $name ($category) - Daily Limit: $limit ==="
  
  # Attempt to win the prize more times than the daily limit
  attempts=$((limit + 2))
  wins=0
  
  for i in $(seq 1 $attempts); do
    echo "  Spin $i:"
    result=$(curl -s -X POST "$API_BASE_URL/admin/test-spin" \
      -H "Content-Type: application/json" \
      -d "{\"admin_password\": \"$ADMIN_PASSWORD\", \"user_id\": \"verify_${id}_${i}\", \"test_date\": \"$TEST_DATE\", \"force_prize_id\": $id}")
    
    prize_name=$(echo $result | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
    
    if [ "$prize_name" = "$name" ]; then
      echo "    ✅ Won $name"
      wins=$((wins + 1))
    else
      echo "    ❌ Won different prize: $prize_name"
    fi
  done
  
  # Check actual win count
  actual_wins=$(sqlite3 pickerwheel_contest.db "
    SELECT COUNT(*) FROM prize_wins 
    WHERE prize_id = $id AND win_date = '$TEST_DATE';
  ")
  
  echo ""
  echo "  Results:"
  echo "  - Expected limit: $limit"
  echo "  - Actual wins: $actual_wins"
  
  if [ "$actual_wins" -le "$limit" ]; then
    echo "  ✅ PASS: Daily limit enforced correctly"
  else
    echo "  ❌ FAIL: Daily limit exceeded"
  fi
  echo ""
done <<< "$PRIZES"

echo "=== VERIFICATION COMPLETE ==="
