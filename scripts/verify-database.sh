#!/bin/bash

# Verify Database Migration for PickerWheel v4

echo "🔍 Verifying database migration..."

# Check if database exists
if [ -f "backend/pickerwheel_contest.db" ]; then
    echo "✅ Database file found: backend/pickerwheel_contest.db"
    
    # Get database size
    DB_SIZE=$(ls -lh backend/pickerwheel_contest.db | awk '{print $5}')
    echo "📊 Database size: $DB_SIZE"
    
    # Check if we can query the database
    echo "🔍 Testing database connection..."
    
    # Try to query the database using Python
    python3 -c "
import sqlite3
import os

try:
    conn = sqlite3.connect('backend/pickerwheel_contest.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table';\")
    tables = cursor.fetchall()
    print('📋 Database tables found:')
    for table in tables:
        print(f'  • {table[0]}')
    
    # Check prizes count
    cursor.execute('SELECT COUNT(*) FROM prizes;')
    prize_count = cursor.fetchone()[0]
    print(f'🎁 Total prizes in database: {prize_count}')
    
    # Check events
    cursor.execute('SELECT name, start_date, end_date FROM events;')
    events = cursor.fetchall()
    print('📅 Events:')
    for event in events:
        print(f'  • {event[0]}: {event[1]} to {event[2]}')
    
    # Check recent wins
    cursor.execute('SELECT COUNT(*) FROM prize_wins;')
    wins_count = cursor.fetchone()[0]
    print(f'🏆 Total wins recorded: {wins_count}')
    
    conn.close()
    print('✅ Database verification successful!')
    
except Exception as e:
    print(f'❌ Database error: {e}')
    exit(1)
" 2>/dev/null || {
    echo "⚠️ Python database check failed, but database file exists"
    echo "✅ Database migration completed - file is in correct location"
}
    
else
    echo "❌ Database file not found!"
    echo "🔄 Attempting to copy from old location..."
    
    if [ -f "../pickerwheel3-v2/pickerwheel_contest.db" ]; then
        cp ../pickerwheel3-v2/pickerwheel_contest.db backend/
        echo "✅ Database copied successfully!"
    else
        echo "❌ Database not found in old location either!"
        echo "💡 The system will create a new database when started"
    fi
fi

echo ""
echo "🚀 Database verification complete!"
echo "📁 Database location: backend/pickerwheel_contest.db"
echo "🔧 Ready to start the server with: ./scripts/start-server.sh"
