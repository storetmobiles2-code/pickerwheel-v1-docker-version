#!/bin/bash

# 🧪 PICKERWHEEL VALIDATION SUITE (CURL VERSION)
# ==============================================
# Comprehensive validation using curl and shell tools

API_BASE="http://localhost:8082"
ADMIN_PASSWORD="myTAdmin2025"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="validation_results_$TIMESTAMP"

echo "🧪 PickerWheel Comprehensive Validation Suite (Curl Version)"
echo "==========================================================="
echo ""

# Create results directory
mkdir -p "$RESULTS_DIR"

# Logging function
log() {
    echo "[$(date +'%H:%M:%S')] $1" | tee -a "$RESULTS_DIR/validation.log"
}

# Test API connectivity
test_api_connectivity() {
    log "🔍 Testing API connectivity..."
    
    if curl -s "$API_BASE/api/admin/database-status?admin_password=$ADMIN_PASSWORD" | jq -e '.success' > /dev/null 2>&1; then
        log "✅ API is accessible"
        return 0
    else
        log "❌ API is not accessible"
        return 1
    fi
}

# Test 1: Daily Data Validation
test_daily_data_validation() {
    log "🧪 TEST 1: Daily Data Validation"
    log "================================"
    
    local results_file="$RESULTS_DIR/daily_data_validation.json"
    echo "[]" > "$results_file"
    
    # Test a sample of dates
    local test_dates=("2025-09-23" "2025-09-24" "2025-09-25" "2025-10-01" "2025-10-15" "2025-10-30")
    
    for date in "${test_dates[@]}"; do
        log "📅 Testing $date..."
        
        local response=$(curl -s "$API_BASE/api/admin/prizes/list?admin_password=$ADMIN_PASSWORD&date=$date")
        local success=$(echo "$response" | jq -r '.success // false')
        local count=$(echo "$response" | jq -r '.total_count // 0')
        
        if [ "$success" = "true" ] && [ "$count" -gt 0 ]; then
            log "✅ $date: $count prizes loaded"
            echo "{\"date\": \"$date\", \"status\": \"SUCCESS\", \"count\": $count}" >> "$results_file.tmp"
        else
            log "❌ $date: Failed to load data"
            echo "{\"date\": \"$date\", \"status\": \"FAILED\", \"count\": 0}" >> "$results_file.tmp"
        fi
    done
    
    # Convert to proper JSON array
    jq -s '.' "$results_file.tmp" > "$results_file"
    rm -f "$results_file.tmp"
    
    log "✅ Daily data validation completed"
}

# Test 2: Spin Alignment Validation
test_spin_alignment() {
    log "🧪 TEST 2: Spin Alignment Validation (20 spins)"
    log "==============================================="
    
    local results_file="$RESULTS_DIR/spin_alignment.json"
    local test_date="2025-09-23"
    local num_spins=20
    
    echo "[]" > "$results_file"
    
    for ((i=1; i<=num_spins; i++)); do
        log "🎯 Spin $i/$num_spins"
        
        # Pre-spin
        local pre_spin_response=$(curl -s -X POST "$API_BASE/api/pre-spin" \
            -H "Content-Type: application/json" \
            -d "{\"user_identifier\": \"validation_$i\", \"date\": \"$test_date\"}")
        
        local pre_spin_success=$(echo "$pre_spin_response" | jq -r '.success // false')
        
        if [ "$pre_spin_success" = "true" ]; then
            local selected_prize=$(echo "$pre_spin_response" | jq -r '.selected_prize // {}')
            local prize_id=$(echo "$selected_prize" | jq -r '.id // null')
            local prize_name=$(echo "$selected_prize" | jq -r '.name // "unknown"')
            local target_segment=$(echo "$pre_spin_response" | jq -r '.target_segment_index // 0')
            
            # Confirm spin
            local spin_response=$(curl -s -X POST "$API_BASE/api/spin" \
                -H "Content-Type: application/json" \
                -d "{\"user_id\": \"validation_$i\", \"selected_prize_id\": $prize_id, \"target_segment_index\": $target_segment, \"date\": \"$test_date\"}")
            
            local spin_success=$(echo "$spin_response" | jq -r '.success // false')
            local popup_prize=$(echo "$spin_response" | jq -r '.prize_won.name // "unknown"')
            local popup_id=$(echo "$spin_response" | jq -r '.prize_won.id // null')
            
            # Check alignment
            local aligned="false"
            if [ "$prize_id" = "$popup_id" ] && [ "$prize_name" = "$popup_prize" ]; then
                aligned="true"
            fi
            
            echo "{\"spin\": $i, \"backend_prize\": \"$prize_name\", \"popup_prize\": \"$popup_prize\", \"aligned\": $aligned, \"segment\": $target_segment}" >> "$results_file.tmp"
            
            if [ "$aligned" = "true" ]; then
                log "✅ Spin $i: Aligned ($prize_name)"
            else
                log "❌ Spin $i: Misaligned (Backend: $prize_name, Popup: $popup_prize)"
            fi
        else
            log "❌ Spin $i: Pre-spin failed"
            echo "{\"spin\": $i, \"error\": \"pre-spin failed\"}" >> "$results_file.tmp"
        fi
        
        sleep 0.2  # Small delay
    done
    
    # Convert to proper JSON array
    jq -s '.' "$results_file.tmp" > "$results_file"
    rm -f "$results_file.tmp"
    
    log "✅ Spin alignment validation completed"
}

# Test 3: Aggressive Selection Logic
test_aggressive_selection() {
    log "🧪 TEST 3: Aggressive Selection Logic (5 cycles × 10 spins)"
    log "========================================================="
    
    local results_file="$RESULTS_DIR/aggressive_selection.json"
    local test_date="2025-09-23"
    local cycles=5
    local spins_per_cycle=10
    
    echo "[]" > "$results_file"
    
    for ((cycle=1; cycle<=cycles; cycle++)); do
        log "🔄 Cycle $cycle/$cycles"
        
        # Reset database for this cycle
        curl -s -X POST "$API_BASE/api/admin/reload-from-master-config" \
            -H "Content-Type: application/json" \
            -d "{\"admin_password\": \"$ADMIN_PASSWORD\", \"date\": \"$test_date\"}" > /dev/null
        
        local rare_wins=0
        local first_rare_spin=0
        local cycle_results=""
        
        for ((spin=1; spin<=spins_per_cycle; spin++)); do
            # Pre-spin
            local pre_spin_response=$(curl -s -X POST "$API_BASE/api/pre-spin" \
                -H "Content-Type: application/json" \
                -d "{\"user_identifier\": \"aggressive_c${cycle}_s${spin}\", \"date\": \"$test_date\"}")
            
            local category=$(echo "$pre_spin_response" | jq -r '.selected_prize.category // "unknown"')
            local prize_name=$(echo "$pre_spin_response" | jq -r '.selected_prize.name // "unknown"')
            local prize_id=$(echo "$pre_spin_response" | jq -r '.selected_prize.id // null')
            
            # Confirm spin
            if [ "$prize_id" != "null" ]; then
                curl -s -X POST "$API_BASE/api/spin" \
                    -H "Content-Type: application/json" \
                    -d "{\"user_id\": \"aggressive_c${cycle}_s${spin}\", \"selected_prize_id\": $prize_id, \"date\": \"$test_date\"}" > /dev/null
            fi
            
            # Track rare/ultra-rare wins
            if [ "$category" = "rare" ] || [ "$category" = "ultra_rare" ]; then
                rare_wins=$((rare_wins + 1))
                if [ $first_rare_spin -eq 0 ]; then
                    first_rare_spin=$spin
                fi
                log "🎯 Cycle $cycle, Spin $spin: $category - $prize_name"
            fi
            
            cycle_results="${cycle_results}\"$category\","
            sleep 0.1
        done
        
        # Remove trailing comma and wrap in array
        cycle_results="[${cycle_results%,}]"
        
        echo "{\"cycle\": $cycle, \"rare_wins\": $rare_wins, \"first_rare_spin\": $first_rare_spin, \"categories\": $cycle_results}" >> "$results_file.tmp"
        
        log "📊 Cycle $cycle: $rare_wins rare/ultra-rare wins, first at spin $first_rare_spin"
    done
    
    # Convert to proper JSON array
    jq -s '.' "$results_file.tmp" > "$results_file"
    rm -f "$results_file.tmp"
    
    log "✅ Aggressive selection testing completed"
}

# Test 4: Inventory Management
test_inventory_management() {
    log "🧪 TEST 4: Inventory Management (30 spins)"
    log "=========================================="
    
    local results_file="$RESULTS_DIR/inventory_management.json"
    local test_date="2025-09-23"
    local num_spins=30
    
    echo "[]" > "$results_file"
    
    # Reset database
    curl -s -X POST "$API_BASE/api/admin/reload-from-master-config" \
        -H "Content-Type: application/json" \
        -d "{\"admin_password\": \"$ADMIN_PASSWORD\", \"date\": \"$test_date\"}" > /dev/null
    
    for ((i=1; i<=num_spins; i++)); do
        # Get inventory before spin
        local before_response=$(curl -s "$API_BASE/api/admin/prizes/list?admin_password=$ADMIN_PASSWORD&date=$test_date")
        
        # Pre-spin
        local pre_spin_response=$(curl -s -X POST "$API_BASE/api/pre-spin" \
            -H "Content-Type: application/json" \
            -d "{\"user_identifier\": \"inventory_$i\", \"date\": \"$test_date\"}")
        
        local prize_id=$(echo "$pre_spin_response" | jq -r '.selected_prize.id // null')
        local prize_name=$(echo "$pre_spin_response" | jq -r '.selected_prize.name // "unknown"')
        
        if [ "$prize_id" != "null" ]; then
            # Get quantity before
            local before_quantity=$(echo "$before_response" | jq -r ".prizes[] | select(.id == $prize_id) | .remaining_quantity")
            
            # Confirm spin
            curl -s -X POST "$API_BASE/api/spin" \
                -H "Content-Type: application/json" \
                -d "{\"user_id\": \"inventory_$i\", \"selected_prize_id\": $prize_id, \"date\": \"$test_date\"}" > /dev/null
            
            # Get inventory after spin
            local after_response=$(curl -s "$API_BASE/api/admin/prizes/list?admin_password=$ADMIN_PASSWORD&date=$test_date")
            local after_quantity=$(echo "$after_response" | jq -r ".prizes[] | select(.id == $prize_id) | .remaining_quantity")
            
            # Check if quantity decremented
            local decremented="false"
            if [ "$after_quantity" -lt "$before_quantity" ]; then
                decremented="true"
            fi
            
            echo "{\"spin\": $i, \"prize\": \"$prize_name\", \"before\": $before_quantity, \"after\": $after_quantity, \"decremented\": $decremented}" >> "$results_file.tmp"
            
            log "📦 Spin $i: $prize_name ($before_quantity → $after_quantity) [$decremented]"
        else
            log "❌ Spin $i: No prize selected"
        fi
        
        sleep 0.1
    done
    
    # Convert to proper JSON array
    jq -s '.' "$results_file.tmp" > "$results_file"
    rm -f "$results_file.tmp"
    
    log "✅ Inventory management testing completed"
}

# Test 5: Sample Date Range Testing
test_date_range() {
    log "🧪 TEST 5: Date Range Testing (Sample dates)"
    log "==========================================="
    
    local results_file="$RESULTS_DIR/date_range_testing.json"
    local test_dates=("2025-09-22" "2025-09-25" "2025-10-01" "2025-10-15" "2025-10-30")
    
    echo "[]" > "$results_file"
    
    for date in "${test_dates[@]}"; do
        log "📅 Testing $date (5 spins)..."
        
        local date_results=""
        local successful_spins=0
        local aligned_spins=0
        
        for ((spin=1; spin<=5; spin++)); do
            # Pre-spin
            local pre_spin_response=$(curl -s -X POST "$API_BASE/api/pre-spin" \
                -H "Content-Type: application/json" \
                -d "{\"user_identifier\": \"date_test_${date}_${spin}\", \"date\": \"$date\"}")
            
            local success=$(echo "$pre_spin_response" | jq -r '.success // false')
            
            if [ "$success" = "true" ]; then
                successful_spins=$((successful_spins + 1))
                
                local prize_id=$(echo "$pre_spin_response" | jq -r '.selected_prize.id // null')
                local prize_name=$(echo "$pre_spin_response" | jq -r '.selected_prize.name // "unknown"')
                local category=$(echo "$pre_spin_response" | jq -r '.selected_prize.category // "unknown"')
                
                # Confirm spin
                local spin_response=$(curl -s -X POST "$API_BASE/api/spin" \
                    -H "Content-Type: application/json" \
                    -d "{\"user_id\": \"date_test_${date}_${spin}\", \"selected_prize_id\": $prize_id, \"date\": \"$date\"}")
                
                local popup_id=$(echo "$spin_response" | jq -r '.prize_won.id // null')
                
                if [ "$prize_id" = "$popup_id" ]; then
                    aligned_spins=$((aligned_spins + 1))
                fi
                
                date_results="${date_results}\"$category\","
            fi
            
            sleep 0.1
        done
        
        # Remove trailing comma and wrap in array
        date_results="[${date_results%,}]"
        
        echo "{\"date\": \"$date\", \"successful_spins\": $successful_spins, \"aligned_spins\": $aligned_spins, \"categories\": $date_results}" >> "$results_file.tmp"
        
        log "📊 $date: $successful_spins/5 successful, $aligned_spins/5 aligned"
    done
    
    # Convert to proper JSON array
    jq -s '.' "$results_file.tmp" > "$results_file"
    rm -f "$results_file.tmp"
    
    log "✅ Date range testing completed"
}

# Generate summary report
generate_summary() {
    log "📋 Generating summary report..."
    
    local summary_file="$RESULTS_DIR/VALIDATION_SUMMARY.md"
    
    cat > "$summary_file" << EOF
# 🧪 PickerWheel Validation Summary

**Generated:** $(date)  
**Test Suite:** Curl-based Validation Suite  
**Results Directory:** $RESULTS_DIR

## 📊 Test Results

### Test 1: Daily Data Validation
$(if [ -f "$RESULTS_DIR/daily_data_validation.json" ]; then
    local total=$(jq length "$RESULTS_DIR/daily_data_validation.json")
    local successful=$(jq '[.[] | select(.status == "SUCCESS")] | length' "$RESULTS_DIR/daily_data_validation.json")
    echo "- **Total Dates Tested:** $total"
    echo "- **Successful:** $successful"
    echo "- **Success Rate:** $(( successful * 100 / total ))%"
else
    echo "- No data available"
fi)

### Test 2: Spin Alignment Validation
$(if [ -f "$RESULTS_DIR/spin_alignment.json" ]; then
    local total=$(jq length "$RESULTS_DIR/spin_alignment.json")
    local aligned=$(jq '[.[] | select(.aligned == true)] | length' "$RESULTS_DIR/spin_alignment.json")
    echo "- **Total Spins:** $total"
    echo "- **Aligned:** $aligned"
    echo "- **Alignment Rate:** $(( aligned * 100 / total ))%"
else
    echo "- No data available"
fi)

### Test 3: Aggressive Selection Logic
$(if [ -f "$RESULTS_DIR/aggressive_selection.json" ]; then
    local cycles=$(jq length "$RESULTS_DIR/aggressive_selection.json")
    local cycles_with_wins=$(jq '[.[] | select(.rare_wins > 0)] | length' "$RESULTS_DIR/aggressive_selection.json")
    local avg_first_win=$(jq '[.[] | select(.first_rare_spin > 0) | .first_rare_spin] | add / length' "$RESULTS_DIR/aggressive_selection.json")
    echo "- **Total Cycles:** $cycles"
    echo "- **Cycles with Rare/Ultra-Rare Wins:** $cycles_with_wins"
    echo "- **Average First Win Spin:** $avg_first_win"
else
    echo "- No data available"
fi)

### Test 4: Inventory Management
$(if [ -f "$RESULTS_DIR/inventory_management.json" ]; then
    local total=$(jq length "$RESULTS_DIR/inventory_management.json")
    local correct=$(jq '[.[] | select(.decremented == true)] | length' "$RESULTS_DIR/inventory_management.json")
    echo "- **Total Spins:** $total"
    echo "- **Correct Decrements:** $correct"
    echo "- **Accuracy:** $(( correct * 100 / total ))%"
else
    echo "- No data available"
fi)

### Test 5: Date Range Testing
$(if [ -f "$RESULTS_DIR/date_range_testing.json" ]; then
    local dates=$(jq length "$RESULTS_DIR/date_range_testing.json")
    local total_spins=$(jq '[.[].successful_spins] | add' "$RESULTS_DIR/date_range_testing.json")
    local total_aligned=$(jq '[.[].aligned_spins] | add' "$RESULTS_DIR/date_range_testing.json")
    echo "- **Dates Tested:** $dates"
    echo "- **Total Successful Spins:** $total_spins"
    echo "- **Total Aligned Spins:** $total_aligned"
    echo "- **Overall Alignment Rate:** $(( total_aligned * 100 / total_spins ))%"
else
    echo "- No data available"
fi)

## 📁 Files Generated

- \`validation.log\` - Complete test execution log
- \`daily_data_validation.json\` - Daily data validation results
- \`spin_alignment.json\` - Spin alignment test results
- \`aggressive_selection.json\` - Aggressive selection test results
- \`inventory_management.json\` - Inventory management test results
- \`date_range_testing.json\` - Date range testing results

## 🎯 Conclusions

$(if [ -f "$RESULTS_DIR/spin_alignment.json" ]; then
    local alignment_rate=$(jq '[.[] | select(.aligned == true)] | length' "$RESULTS_DIR/spin_alignment.json")
    local total_spins=$(jq length "$RESULTS_DIR/spin_alignment.json")
    local percentage=$(( alignment_rate * 100 / total_spins ))
    
    if [ $percentage -ge 95 ]; then
        echo "✅ **SYSTEM READY FOR PRODUCTION** - Alignment rate: $percentage%"
    elif [ $percentage -ge 80 ]; then
        echo "⚠️ **SYSTEM NEEDS MINOR ADJUSTMENTS** - Alignment rate: $percentage%"
    else
        echo "❌ **SYSTEM REQUIRES ATTENTION** - Alignment rate: $percentage%"
    fi
else
    echo "⚠️ **INCOMPLETE TESTING** - Some tests did not complete successfully"
fi)

---

*Generated by PickerWheel Validation Suite (Curl Version)*
EOF

    log "✅ Summary report generated: $summary_file"
}

# Main execution
main() {
    log "🚀 Starting PickerWheel Validation Suite"
    
    # Test API connectivity
    if ! test_api_connectivity; then
        log "❌ Cannot proceed without API access"
        exit 1
    fi
    
    # Run all tests
    test_daily_data_validation
    test_spin_alignment
    test_aggressive_selection
    test_inventory_management
    test_date_range
    
    # Generate summary
    generate_summary
    
    log "🎉 Validation suite completed!"
    log "📁 Results saved in: $RESULTS_DIR/"
    log "📋 Summary report: $RESULTS_DIR/VALIDATION_SUMMARY.md"
    
    echo ""
    echo "🎯 QUICK RESULTS:"
    echo "================="
    if [ -f "$RESULTS_DIR/VALIDATION_SUMMARY.md" ]; then
        tail -20 "$RESULTS_DIR/VALIDATION_SUMMARY.md"
    fi
}

# Check dependencies
if ! command -v jq &> /dev/null; then
    echo "❌ jq is required but not installed. Please install jq first."
    echo "   On macOS: brew install jq"
    echo "   On Ubuntu: sudo apt-get install jq"
    exit 1
fi

if ! command -v curl &> /dev/null; then
    echo "❌ curl is required but not installed."
    exit 1
fi

# Run main function
main "$@"
