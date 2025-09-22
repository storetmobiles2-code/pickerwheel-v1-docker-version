#!/bin/bash
# Script to start the backend with a clean database

echo "=== STARTING BACKEND WITH CLEAN DATABASE ==="
echo ""

# First, stop any existing backend processes
echo "🔄 Stopping any existing backend processes..."
./stop_backend.sh > /dev/null

# Delete the database file
echo ""
echo "🔄 Deleting database file..."
if [ -f "backend/pickerwheel_contest.db" ]; then
    rm -f backend/pickerwheel_contest.db
    echo "Database file deleted."
else
    echo "No database file found."
fi

# Modify the port in backend-api.py
echo ""
echo "🔄 Ensuring port is set to 9080..."
sed -i '' 's/port=[0-9]*/port=9080/g' backend/backend-api.py

# Start the backend
echo ""
echo "🔄 Starting backend..."
cd backend
python3 backend-api.py &

# Wait for the server to start
echo ""
echo "Waiting for server to start..."
sleep 2

# Check if the server is running
PORT=9080  # Use the fixed port

echo "Checking if server is running on port $PORT..."
for i in {1..5}; do
    if curl -s http://localhost:$PORT/api/prizes/available > /dev/null; then
        echo "✅ Server is running on port $PORT."
        exit 0
    else
        echo "Waiting... ($i/5)"
        sleep 1
    fi
done

echo "⚠️ Server may not have started properly. Check logs."
