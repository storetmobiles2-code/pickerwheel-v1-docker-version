#!/bin/bash
# Script to start the daily backend

echo "=== STARTING DAILY PICKERWHEEL BACKEND ==="
echo ""

# First, stop any existing backend processes
echo "🔄 Stopping any existing backend processes..."
pkill -f daily_database_backend.py > /dev/null 2>&1

# Check if daily CSV files exist
echo "🔄 Checking daily CSV files..."
if [ ! -d "daily_csvs" ]; then
    echo "❌ Daily CSV directory not found. Generating daily CSV files..."
    python3 scripts/generate_daily_csv.py
fi

# Check if we have CSV files for today
TODAY=$(date +%Y-%m-%d)
CSV_FILE="daily_csvs/prizes_${TODAY}.csv"

if [ ! -f "$CSV_FILE" ]; then
    echo "⚠️  No CSV file for today ($TODAY). Available files:"
    ls -la daily_csvs/prizes_*.csv | head -5
    echo ""
    echo "Using 2025-10-02 as test date..."
fi

echo "📊 Daily CSV files available:"
ls daily_csvs/prizes_*.csv | wc -l | xargs echo "   Total files:"

# Start the daily backend
echo ""
echo "🔄 Starting daily backend on port 9082..."
cd backend
python3 daily_database_backend.py &

# Wait for the server to start
echo ""
echo "Waiting for server to start..."
sleep 2

# Check if the server is running
PORT=9082  # Use the daily backend port

echo "Checking if server is running on port $PORT..."
for i in {1..5}; do
    if curl -s http://localhost:$PORT/api/prizes/wheel-display > /dev/null; then
        echo "✅ Daily backend is running on port $PORT."
        echo ""
        echo "🌐 Access the app at: http://localhost:$PORT"
        echo "📊 Daily system with transactional history and inventory tracking"
        exit 0
    else
        echo "Waiting... ($i/5)"
        sleep 1
    fi
done

echo "⚠️ Server may not have started properly. Check logs."
