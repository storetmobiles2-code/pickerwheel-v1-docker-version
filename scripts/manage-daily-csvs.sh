#!/bin/bash
# Script to manage daily CSV files

echo "=== DAILY CSV MANAGEMENT ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to show usage
show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  generate    - Generate daily CSV files from itemlist_dates.txt"
    echo "  status      - Show status of daily CSV files"
    echo "  clean       - Clean old CSV files (keep last 7 days)"
    echo "  verify      - Verify CSV files for specific dates"
    echo "  help        - Show this help message"
    echo ""
}

# Function to generate CSV files
generate_csvs() {
    echo "🔄 Generating daily CSV files..."
    python3 scripts/generate_daily_csv.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Daily CSV files generated successfully${NC}"
    else
        echo -e "${RED}❌ Failed to generate CSV files${NC}"
        exit 1
    fi
}

# Function to show status
show_status() {
    echo "📊 Daily CSV Files Status"
    echo "========================="
    
    if [ ! -d "daily_csvs" ]; then
        echo -e "${RED}❌ Daily CSV directory not found${NC}"
        return 1
    fi
    
    TOTAL_FILES=$(ls daily_csvs/prizes_*.csv 2>/dev/null | wc -l)
    echo "Total CSV files: $TOTAL_FILES"
    
    if [ $TOTAL_FILES -gt 0 ]; then
        echo ""
        echo "Date range:"
        FIRST_FILE=$(ls daily_csvs/prizes_*.csv | head -1 | sed 's/.*prizes_\(.*\)\.csv/\1/')
        LAST_FILE=$(ls daily_csvs/prizes_*.csv | tail -1 | sed 's/.*prizes_\(.*\)\.csv/\1/')
        echo "  From: $FIRST_FILE"
        echo "  To:   $LAST_FILE"
        
        echo ""
        echo "Recent files:"
        ls -la daily_csvs/prizes_*.csv | tail -5 | while read line; do
            echo "  $line"
        done
        
        # Check today's file
        TODAY=$(date +%Y-%m-%d)
        TODAY_FILE="daily_csvs/prizes_${TODAY}.csv"
        if [ -f "$TODAY_FILE" ]; then
            TODAY_PRIZES=$(wc -l < "$TODAY_FILE")
            echo ""
            echo -e "${GREEN}✅ Today's file ($TODAY): $TODAY_PRIZES lines${NC}"
        else
            echo ""
            echo -e "${YELLOW}⚠️  No CSV file for today ($TODAY)${NC}"
        fi
    fi
}

# Function to clean old files
clean_old_files() {
    echo "🧹 Cleaning old CSV files (keeping last 7 days)..."
    
    if [ ! -d "daily_csvs" ]; then
        echo -e "${RED}❌ Daily CSV directory not found${NC}"
        return 1
    fi
    
    # Keep files from the last 7 days
    CUTOFF_DATE=$(date -d "7 days ago" +%Y-%m-%d)
    
    REMOVED_COUNT=0
    for file in daily_csvs/prizes_*.csv; do
        if [ -f "$file" ]; then
            FILE_DATE=$(basename "$file" | sed 's/prizes_\(.*\)\.csv/\1/')
            if [[ "$FILE_DATE" < "$CUTOFF_DATE" ]]; then
                echo "  Removing: $file"
                rm "$file"
                ((REMOVED_COUNT++))
            fi
        fi
    done
    
    if [ $REMOVED_COUNT -eq 0 ]; then
        echo -e "${GREEN}✅ No old files to remove${NC}"
    else
        echo -e "${GREEN}✅ Removed $REMOVED_COUNT old files${NC}"
    fi
}

# Function to verify specific dates
verify_dates() {
    echo "🔍 Verifying CSV files for specific dates..."
    echo ""
    
    # Test dates with known prizes
    TEST_DATES=("2025-10-02" "2025-10-20" "2025-10-21")
    
    for date in "${TEST_DATES[@]}"; do
        FILE="daily_csvs/prizes_${date}.csv"
        if [ -f "$FILE" ]; then
            PRIZE_COUNT=$(tail -n +2 "$FILE" | wc -l)
            echo -e "  ${GREEN}✅ $date: $PRIZE_COUNT prizes${NC}"
            
            # Show category breakdown
            CATEGORIES=$(tail -n +2 "$FILE" | cut -d',' -f2 | sort | uniq -c)
            echo "     Categories: $CATEGORIES"
        else
            echo -e "  ${RED}❌ $date: File not found${NC}"
        fi
    done
}

# Main script logic
case "${1:-help}" in
    "generate")
        generate_csvs
        ;;
    "status")
        show_status
        ;;
    "clean")
        clean_old_files
        ;;
    "verify")
        verify_dates
        ;;
    "help"|*)
        show_usage
        ;;
esac
