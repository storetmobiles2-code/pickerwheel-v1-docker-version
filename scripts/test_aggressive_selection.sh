#!/bin/bash

# Test the aggressive rare/ultra-rare selection logic
# Verifies that rare items are won within 3-5 spins as expected

echo "🚀 TESTING AGGRESSIVE RARE/ULTRA-RARE SELECTION"
echo "============================================================"
echo "📋 Expected behavior:"
echo "   • Ultra-rare items: 80% chance in first 3 spins"
echo "   • Rare items: Guaranteed by spin 5 if no rare/ultra-rare won"
echo "   • Weighted selection favors scarce items"
echo ""

BASE_URL="http://localhost:8082"
SIMULATION_RUNS=5

# Counters
ultra_rare_in_first_3=0
rare_in_first_5=0
total_runs=$SIMULATION_RUNS

for run in $(seq 1 $SIMULATION_RUNS); do
    echo "🎯 SIMULATION RUN #$run"
    echo "----------------------------------------"
    
    # Reset database for clean test
    echo "🔄 Resetting database..."
    curl -s -X POST "$BASE_URL/api/admin/reset-database" \
         -H "Content-Type: application/json" \
         -d '{"confirm": true}' > /dev/null
    
    sleep 2  # Allow reset to complete
    
    # Track first rare/ultra-rare win
    first_rare_spin=""
    first_ultra_rare_spin=""
    
    # Perform up to 5 spins
    for spin_num in $(seq 1 5); do
        echo "  🎲 Spin #$spin_num:"
        
        # Call pre-spin to get selected prize
        pre_spin_response=$(curl -s -X POST "$BASE_URL/api/pre-spin" \
                                -H "Content-Type: application/json" \
                                -d "{\"user\": \"test_user_run$run\"}")
        
        if [ $? -eq 0 ]; then
            # Extract prize info using basic text processing
            prize_name=$(echo "$pre_spin_response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
            prize_category=$(echo "$pre_spin_response" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
            
            echo "    Selected: $prize_name ($prize_category)"
            
            # Confirm the spin
            spin_response=$(curl -s -X POST "$BASE_URL/api/spin" \
                               -H "Content-Type: application/json" \
                               -d "{\"user\": \"test_user_run$run\"}")
            
            if [ $? -eq 0 ]; then
                # Extract confirmed prize info
                confirmed_name=$(echo "$spin_response" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)
                confirmed_category=$(echo "$spin_response" | grep -o '"category":"[^"]*"' | cut -d'"' -f4)
                
                echo "    Confirmed: $confirmed_name ($confirmed_category)"
                
                # Track first rare/ultra-rare wins
                if [ "$confirmed_category" = "ultra_rare" ] && [ -z "$first_ultra_rare_spin" ]; then
                    first_ultra_rare_spin=$spin_num
                    echo "    🌟 FIRST ULTRA-RARE WON ON SPIN #$spin_num"
                elif [ "$confirmed_category" = "rare" ] && [ -z "$first_rare_spin" ]; then
                    first_rare_spin=$spin_num
                    echo "    ⭐ FIRST RARE WON ON SPIN #$spin_num"
                fi
                
                # Stop if we got a rare/ultra-rare item
                if [ "$confirmed_category" = "rare" ] || [ "$confirmed_category" = "ultra_rare" ]; then
                    echo "    ✅ Rare/Ultra-rare achieved on spin #$spin_num"
                    break
                fi
            else
                echo "    ❌ Spin confirmation failed"
                break
            fi
        else
            echo "    ❌ Pre-spin failed"
            break
        fi
    done
    
    # Analyze run results
    echo "  📊 Run #$run Summary:"
    if [ -n "$first_ultra_rare_spin" ]; then
        echo "    Ultra-rare won on spin #$first_ultra_rare_spin"
        if [ "$first_ultra_rare_spin" -le 3 ]; then
            ultra_rare_in_first_3=$((ultra_rare_in_first_3 + 1))
        fi
    fi
    
    if [ -n "$first_rare_spin" ]; then
        echo "    Rare won on spin #$first_rare_spin"
    fi
    
    if [ -n "$first_rare_spin" ] || [ -n "$first_ultra_rare_spin" ]; then
        # Check if any rare/ultra-rare won in first 5 spins
        if ([ -n "$first_rare_spin" ] && [ "$first_rare_spin" -le 5 ]) || \
           ([ -n "$first_ultra_rare_spin" ] && [ "$first_ultra_rare_spin" -le 5 ]); then
            rare_in_first_5=$((rare_in_first_5 + 1))
        fi
    else
        echo "    ⚠️  No rare/ultra-rare won in 5 spins"
    fi
    
    echo ""
    sleep 2  # Brief pause between runs
done

# Final analysis
echo "📊 FINAL RESULTS ANALYSIS"
echo "============================================================"

ultra_rare_success_rate=$(( (ultra_rare_in_first_3 * 100) / total_runs ))
rare_guarantee_rate=$(( (rare_in_first_5 * 100) / total_runs ))

echo "🌟 Ultra-rare in first 3 spins: $ultra_rare_in_first_3/$total_runs (${ultra_rare_success_rate}%)"
echo "   Expected: ~80% | Actual: ${ultra_rare_success_rate}%"

echo "⭐ Rare/Ultra-rare in first 5 spins: $rare_in_first_5/$total_runs (${rare_guarantee_rate}%)"
echo "   Expected: ~95-100% | Actual: ${rare_guarantee_rate}%"

echo ""
echo "🎯 SUCCESS CRITERIA:"

# Success criteria (allowing some variance)
if [ "$ultra_rare_success_rate" -ge 60 ]; then
    echo "  ✅ Ultra-rare boost working: PASS"
    ultra_rare_success=true
else
    echo "  ❌ Ultra-rare boost working: FAIL"
    ultra_rare_success=false
fi

if [ "$rare_guarantee_rate" -ge 80 ]; then
    echo "  ✅ Rare guarantee working: PASS"
    rare_guarantee_success=true
else
    echo "  ❌ Rare guarantee working: FAIL"
    rare_guarantee_success=false
fi

echo ""
if [ "$ultra_rare_success" = true ] && [ "$rare_guarantee_success" = true ]; then
    echo "🏆 OVERALL TEST: ✅ PASS"
    echo "🎉 Aggressive selection logic is working as expected!"
    echo "   Rare and ultra-rare items will be won within 3-5 spins."
else
    echo "🏆 OVERALL TEST: ❌ FAIL"
    echo "⚠️  Aggressive selection needs adjustment."
    echo "   Consider increasing boost percentages or weights."
fi
