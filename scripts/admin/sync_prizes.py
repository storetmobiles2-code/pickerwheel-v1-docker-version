#!/usr/bin/env python3
"""
Sync Prizes Tool for PickerWheel Contest

This script syncs the prizes table with the CSV configuration.
"""

import os
import sys
import sqlite3
import csv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_prizes_from_csv(csv_path, db_path):
    """Sync prizes table with CSV configuration"""
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Read CSV file
    with open(csv_path, 'r', encoding='utf-8') as file:
        # Filter out comments and empty lines
        lines = [line for line in file if line.strip() and not line.strip().startswith('#')]
        
        # Create CSV reader
        reader = csv.DictReader(lines)
        
        # Get column names
        name_key = next((k for k in reader.fieldnames if 'item' in k.lower() or 'name' in k.lower()), 'Item/Combo Name')
        category_key = next((k for k in reader.fieldnames if 'category' in k.lower()), 'Category')
        emoji_key = next((k for k in reader.fieldnames if 'emoji' in k.lower()), 'Emoji')
        description_key = next((k for k in reader.fieldnames if 'desc' in k.lower()), 'Description')
        
        # Get existing prizes
        cursor.execute("SELECT id, name FROM prizes")
        existing_prizes = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
        
        # Get category IDs
        cursor.execute("SELECT id, name FROM prize_categories")
        categories = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
        
        # Process each row
        new_prizes = []
        updated_prizes = []
        
        for row in reader:
            # Skip empty rows
            if not row or not any(row.values()):
                continue
                
            # Get prize data
            name = row[name_key].strip() if name_key in row else ''
            if not name:
                continue
                
            category = row[category_key].strip().lower().replace(' ', '_') if category_key in row else 'common'
            emoji = row[emoji_key].strip() if emoji_key in row and row[emoji_key].strip() else '🎁'
            description = row[description_key].strip() if description_key in row and row[description_key].strip() else f'{category.title()} prize: {name}'
            
            # Determine prize type
            prize_type = 'combo' if '+' in name else 'single'
            
            # Get category ID
            category_id = categories.get(category, 1)  # Default to common (ID 1) if category not found
            
            # Check if prize exists
            prize_id = None
            for existing_name, existing_id in existing_prizes.items():
                if name.lower() == existing_name or name.lower() in existing_name or existing_name in name.lower():
                    prize_id = existing_id
                    break
            
            if prize_id:
                # Update existing prize
                cursor.execute("""
                    UPDATE prizes
                    SET name = ?, category_id = ?, type = ?, emoji = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, category_id, prize_type, emoji, description, prize_id))
                updated_prizes.append(name)
            else:
                # Add new prize
                cursor.execute("""
                    INSERT INTO prizes (name, category_id, type, emoji, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, category_id, prize_type, emoji, description))
                new_prizes.append(name)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logger.info(f"Added {len(new_prizes)} new prizes: {', '.join(new_prizes)}")
        logger.info(f"Updated {len(updated_prizes)} existing prizes")
        
        return {
            'new_prizes': new_prizes,
            'updated_prizes': updated_prizes
        }

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sync_prizes.py csv_path db_path")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    db_path = sys.argv[2]
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found")
        sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"Error: Database file '{db_path}' not found")
        sys.exit(1)
    
    sync_prizes_from_csv(csv_path, db_path)
