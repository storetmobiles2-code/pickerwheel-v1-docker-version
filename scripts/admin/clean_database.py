#!/usr/bin/env python3
"""
Clean Database Tool for PickerWheel Contest

This script cleans up the database to match the CSV configuration.
"""

import os
import sys
import sqlite3
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_database(csv_path, db_path):
    """Clean up the database to match the CSV configuration"""
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Read CSV file to get valid prize names
    valid_prizes = []
    with open(csv_path, 'r', encoding='utf-8') as file:
        # Skip comments and empty lines
        lines = [line for line in file if line.strip() and not line.strip().startswith('#')]
        
        # Create CSV reader
        reader = csv.reader(lines)
        
        # Skip header
        next(reader, None)
        
        # Get prize names from CSV
        for row in reader:
            if row and len(row) >= 1:
                prize_name = row[0].strip()
                if prize_name:
                    valid_prizes.append(prize_name.lower())
    
    # Get all prizes from database
    cursor.execute("SELECT id, name FROM prizes")
    db_prizes = {row['id']: row['name'].lower() for row in cursor.fetchall()}
    
    # Find prizes to remove (in database but not in CSV)
    prizes_to_remove = []
    for prize_id, prize_name in db_prizes.items():
        # Check if prize is in CSV (using fuzzy matching)
        found = False
        for valid_prize in valid_prizes:
            if valid_prize in prize_name or prize_name in valid_prize:
                found = True
                break
        
        if not found:
            prizes_to_remove.append((prize_id, prize_name))
    
    # Remove prizes that are not in the CSV
    for prize_id, prize_name in prizes_to_remove:
        logger.info(f"Removing prize: {prize_name} (ID: {prize_id})")
        
        # Delete from prize_inventory
        cursor.execute("DELETE FROM prize_inventory WHERE prize_id = ?", (prize_id,))
        
        # Delete from prize_wins
        cursor.execute("DELETE FROM prize_wins WHERE prize_id = ?", (prize_id,))
        
        # Delete from prizes
        cursor.execute("DELETE FROM prizes WHERE id = ?", (prize_id,))
    
    # Commit changes
    conn.commit()
    conn.close()
    
    logger.info(f"Removed {len(prizes_to_remove)} prizes from database")
    return prizes_to_remove

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python clean_database.py csv_path db_path")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    db_path = sys.argv[2]
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found")
        sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found")
        sys.exit(1)
    
    clean_database(csv_path, db_path)
