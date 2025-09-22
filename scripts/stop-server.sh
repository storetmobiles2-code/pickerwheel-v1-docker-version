#!/bin/bash
# Script to stop all backend processes

echo "=== STOPPING ALL BACKEND PROCESSES ==="
echo ""

# Find all Python processes running backend-api.py
echo "🔍 Finding backend processes..."
PIDS=$(ps aux | grep "[p]ython" | grep "backend-api.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No backend processes found."
    exit 0
fi

# Print the processes
echo "Found processes:"
for PID in $PIDS; do
    echo "  - PID: $PID"
done

# Kill the processes
echo ""
echo "🔄 Killing processes..."
for PID in $PIDS; do
    kill -9 $PID
    echo "  - Killed process $PID"
done

# Check if any processes are still running
sleep 1
REMAINING=$(ps aux | grep "[p]ython" | grep "backend-api.py" | awk '{print $2}')
if [ -z "$REMAINING" ]; then
    echo ""
    echo "✅ All backend processes stopped successfully."
else
    echo ""
    echo "⚠️ Some processes are still running:"
    for PID in $REMAINING; do
        echo "  - PID: $PID"
    done
    echo "Try running this script again or manually kill these processes."
fi

# Check for processes using ports 9080, 9081, 9082, 9083
echo ""
echo "🔍 Checking for processes using backend ports..."
for PORT in 9080 9081 9082 9083; do
    PROC=$(lsof -i :$PORT | grep LISTEN)
    if [ ! -z "$PROC" ]; then
        echo "Port $PORT is in use by:"
        echo "$PROC"
        PID=$(echo "$PROC" | awk '{print $2}')
        echo "Killing process $PID..."
        kill -9 $PID
    else
        echo "Port $PORT is free."
    fi
done

echo ""
echo "Done."
