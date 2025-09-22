#!/usr/bin/env python3
"""
Database Reset Script
Drops and recreates all tables with standardized schema
"""

import sqlite3
import os
import sys

def reset_database():
    """Reset the database with new schema"""
    db_path = 'pickerwheel_contest.db'
    
    if os.path.exists(db_path):
        print(f"🗑️  Removing existing database: {db_path}")
        os.remove(db_path)
    
    print("🔄 Creating new database with standardized schema...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create daily_prizes table with standardized schema
        cursor.execute('''
            CREATE TABLE daily_prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                prize_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                daily_limit INTEGER NOT NULL,
                available_dates TEXT,
                emoji TEXT DEFAULT '🎁',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create daily_inventory table with standardized schema
        cursor.execute('''
            CREATE TABLE daily_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                prize_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                initial_quantity INTEGER NOT NULL,
                remaining_quantity INTEGER NOT NULL,
                daily_limit INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, prize_id)
            )
        ''')
        
        # Create daily_transactions table with standardized schema
        cursor.execute('''
            CREATE TABLE daily_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                prize_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                user_identifier TEXT,
                transaction_type TEXT DEFAULT 'win',
                quantity INTEGER DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create daily_stats table
        cursor.execute('''
            CREATE TABLE daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_prizes INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                unique_users INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX idx_daily_prizes_date ON daily_prizes(date)')
        cursor.execute('CREATE INDEX idx_daily_inventory_date ON daily_inventory(date)')
        cursor.execute('CREATE INDEX idx_daily_transactions_date ON daily_transactions(date)')
        cursor.execute('CREATE INDEX idx_daily_stats_date ON daily_stats(date)')
        
        conn.commit()
        print("✅ Database created successfully with standardized schema!")
        
        # Show table structure
        print("\n📋 Database Schema:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"\n🔹 Table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    success = reset_database()
    sys.exit(0 if success else 1)
