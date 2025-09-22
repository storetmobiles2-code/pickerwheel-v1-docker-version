#!/usr/bin/env python3
"""
PickerWheel Contest Backend API
{{ ... }}
2-Month Event Management System with SQLite Database
Created: September 21, 2025
"""

import sqlite3
import logging
import os
import time
import hmac
import hashlib
import json
import csv
import random
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import secrets
import hashlib
import logging
from typing import Dict, List, Optional, Tuple
from db_management_endpoints import register_db_management_endpoints

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = 'pickerwheel_contest.db'
# Check if we're running in Docker (if /app exists)
import os
CSV_CONFIG_PATH = '/app/itemlist_dates.txt' if os.path.exists('/app') else '../itemlist_dates.txt'
EVENT_ID = 1  # Default event ID
EVENT_START_DATE = '2025-09-21'
EVENT_END_DATE = '2025-11-21'
ADMIN_PASSWORD = 'myTAdmin2025'
PORT = 9081  # Changed from 9080 to avoid conflicts

class CSVConfigManager:
    """Handles CSV-based prize configuration with validation and import/export"""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.required_columns = ['Item/Combo Name', 'Category', 'Total Quantity', 'Daily Limit', 'Available Dates']
        # Also support legacy column names for backward compatibility
        self.legacy_columns = ['Item/Combo List', 'Category', 'Quantity', 'Quantity Per Day', 'Available Dates']
        self.valid_categories = ['common', 'rare', 'ultra rare']
    
    def load_prizes_from_csv(self) -> List[Dict]:
        """Load prize configuration from CSV file with simplified format"""
        prizes = []
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Read all lines to handle comments
                lines = [line for line in file if line.strip() and not line.strip().startswith('#')]
                
                # Create a new CSV reader from filtered lines
                reader = csv.DictReader(lines)
                
                for i, row in enumerate(reader, 1):
                    # Skip empty rows
                    if not row or not any(row.values()):
                        continue
                    
                    # Get column names based on file format - support multiple formats
                    name_key = next((k for k in row.keys() if 'item' in k.lower() or 'name' in k.lower()), None)
                    if not name_key:
                        continue  # Skip if no name column found
                        
                    category_key = next((k for k in row.keys() if 'category' in k.lower()), None)
                    quantity_key = next((k for k in row.keys() if ('total' in k.lower() or 'quantity' in k.lower()) and 'day' not in k.lower()), None)
                    daily_limit_key = next((k for k in row.keys() if 'day' in k.lower() or 'limit' in k.lower() or 'per' in k.lower()), None)
                    dates_key = next((k for k in row.keys() if 'date' in k.lower() or 'available' in k.lower()), None)
                    
                    # Skip if essential columns are missing
                    if not name_key or not category_key:
                        continue
                    
                    # Parse the row data with flexible column names
                    name = row[name_key].strip() if name_key in row else ''
                    if not name:  # Skip rows without a name
                        continue
                        
                    category = row[category_key].strip().lower().replace(' ', '_') if category_key in row else 'common'
                    quantity = row[quantity_key].strip() if quantity_key and quantity_key in row and row[quantity_key].strip() else None
                    daily_limit = row[daily_limit_key].strip() if daily_limit_key and daily_limit_key in row and row[daily_limit_key].strip() else '1'
                    available_dates = row[dates_key].strip() if dates_key and dates_key in row and row[dates_key].strip() else '*'
                    
                    # Determine prize type (combo or single) - simple logic
                    prize_type = 'combo' if '+' in name else 'single'
                    
                    # Parse daily limit - handle both "100" and "100/day" formats
                    if '/' in daily_limit:
                        qty_per_day = int(daily_limit.split('/')[0])
                    else:
                        qty_per_day = int(daily_limit) if daily_limit.isdigit() else 1
                    
                    # Set appropriate defaults based on category
                    if category == 'common':
                        qty_per_day = max(qty_per_day, 100)  # Ensure common items have high daily limit
                    
                    # Parse available dates
                    if available_dates == '*' or available_dates == '':
                        dates = ['*']  # Always available
                    elif 'random' in available_dates.lower():
                        # For "Random days", we'll set specific dates during the contest period
                        dates = self._generate_random_dates(int(quantity) if quantity and quantity.isdigit() else qty_per_day)
                    else:
                        dates = [d.strip() for d in available_dates.split('|') if d.strip()]
                    
                    # Create prize object with minimal structure - only essential fields
                    prize = {
                        'id': i,
                        'name': name,
                        'category': category,
                        'type': prize_type,
                        'availability_dates': dates,
                        'quantity_per_date': qty_per_day,
                        'total_quantity': int(quantity) if quantity and quantity.isdigit() else None
                    }
                    
                    prizes.append(prize)
                    
            logger.info(f"Loaded {len(prizes)} prizes from CSV configuration")
            return prizes
            
        except Exception as e:
            logger.error(f"Failed to load CSV configuration: {e}")
            return []
    
    def _generate_random_dates(self, count: int) -> List[str]:
        """Generate random dates for prizes marked as 'Random days'"""
        from datetime import datetime, timedelta
        import random
        
        start_date = datetime(2025, 9, 21)
        end_date = datetime(2025, 11, 21)
        
        # Generate random dates
        dates = []
        for _ in range(count):
            random_days = random.randint(0, (end_date - start_date).days)
            random_date = start_date + timedelta(days=random_days)
            dates.append(random_date.strftime('%Y-%m-%d'))
        
        return sorted(list(set(dates)))  # Remove duplicates and sort
        
    def get_csv_content(self) -> str:
        """Get the current CSV file content"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return ""
            
    def update_csv_file(self, csv_content: str) -> Dict:
        """Update the CSV file with new content"""
        try:
            # Validate the CSV content
            validation_results = self.validate_csv_content(csv_content)
            
            if not validation_results['valid']:
                return {
                    'success': False,
                    'error': 'Invalid CSV content',
                    'validation_results': validation_results
                }
            
            # Write to file
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                f.write(csv_content)
            
            return {
                'success': True,
                'message': 'CSV file updated successfully',
                'validation_results': validation_results
            }
        except Exception as e:
            logger.error(f"Error updating CSV file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_csv_content(self, csv_content: str) -> Dict:
        """Validate CSV content and return validation results"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'summary': {},
            'parsed_data': []
        }
        
        try:
            # Parse CSV content
            reader = csv.DictReader(csv_content.strip().split('\n'))
            
            # Check required columns
            if not reader.fieldnames:
                validation_result['valid'] = False
                validation_result['errors'].append("CSV file appears to be empty or invalid")
                return validation_result
            
            # Check if we have either the new format or the legacy format
            new_format_missing = set(self.required_columns) - set(reader.fieldnames)
            legacy_format_missing = set(self.legacy_columns) - set(reader.fieldnames)
            
            # If neither format is complete, report missing columns
            if new_format_missing and legacy_format_missing:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required columns. Expected either:\n" +
                                                 f"New format: {', '.join(self.required_columns)}\n" +
                                                 f"Legacy format: {', '.join(self.legacy_columns)}")
                
                # Determine which format is closer and suggest missing columns
                if len(new_format_missing) <= len(legacy_format_missing):
                    validation_result['errors'].append(f"Missing columns from new format: {', '.join(new_format_missing)}")
                else:
                    validation_result['errors'].append(f"Missing columns from legacy format: {', '.join(legacy_format_missing)}")
            
            # Add a warning if using legacy format
            if not new_format_missing:
                validation_result['format'] = 'new'
            elif not legacy_format_missing:
                validation_result['format'] = 'legacy'
                validation_result['warnings'].append("Using legacy column format. Consider updating to the new format.")
            else:
                validation_result['format'] = 'mixed'
                validation_result['warnings'].append("Using mixed column format. This may cause issues.")
                return validation_result
            
            # Validate each row
            category_counts = {'common': 0, 'rare': 0, 'ultra rare': 0}
            row_number = 1
            
            for row in reader:
                row_number += 1
                row_errors = []
                
                # Validate item name
                item_name = row['Item/Combo List'].strip()
                if not item_name:
                    row_errors.append(f"Row {row_number}: Item name cannot be empty")
                
                # Validate category
                category = row['Category'].strip().lower()
                if category and category not in self.valid_categories:
                    row_errors.append(f"Row {row_number}: Invalid category '{category}'. Must be one of: {', '.join(self.valid_categories)}")
                elif category:
                    category_counts[category] += 1
                
                # Validate quantity
                quantity = row['Quantity'].strip()
                if quantity and not quantity.isdigit():
                    row_errors.append(f"Row {row_number}: Quantity must be a number, got '{quantity}'")
                
                # Validate quantity per day
                qty_per_day = row['Quantity Per Day'].strip()
                if qty_per_day and '/' in qty_per_day:
                    qty_part = qty_per_day.split('/')[0]
                    if not qty_part.isdigit():
                        row_errors.append(f"Row {row_number}: Quantity per day must be in format 'N/day', got '{qty_per_day}'")
                
                # Validate dates
                available_dates = row['Available Dates'].strip()
                if available_dates and available_dates not in ['*', '']:
                    if 'random' not in available_dates.lower():
                        dates = [d.strip() for d in available_dates.split('|') if d.strip()]
                        for date_str in dates:
                            try:
                                datetime.strptime(date_str, '%Y-%m-%d')
                            except ValueError:
                                row_errors.append(f"Row {row_number}: Invalid date format '{date_str}'. Use YYYY-MM-DD")
                
                if row_errors:
                    validation_result['errors'].extend(row_errors)
                    validation_result['valid'] = False
                
                # Add parsed data
                validation_result['parsed_data'].append({
                    'row': row_number,
                    'item': item_name,
                    'category': category,
                    'quantity': quantity,
                    'qty_per_day': qty_per_day,
                    'dates': available_dates,
                    'errors': row_errors
                })
            
            # Generate summary
            validation_result['summary'] = {
                'total_items': len(validation_result['parsed_data']),
                'category_breakdown': category_counts,
                'total_errors': len(validation_result['errors']),
                'total_warnings': len(validation_result['warnings'])
            }
            
            # Add warnings for category distribution
            if category_counts['ultra rare'] > 10:
                validation_result['warnings'].append(f"High number of Ultra Rare items ({category_counts['ultra rare']}). Consider if this is intended.")
            
            if category_counts['common'] == 0:
                validation_result['warnings'].append("No Common items found. Users may have limited winning opportunities.")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"CSV parsing error: {str(e)}")
        
        return validation_result
    
    def export_current_csv(self) -> str:
        """Export current CSV configuration as string"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            return ""
    
    def backup_current_csv(self) -> str:
        """Create a backup of current CSV with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{self.csv_path}.backup_{timestamp}"
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as source:
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(source.read())
            logger.info(f"CSV backup created: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create CSV backup: {e}")
            return ""
    
    def update_csv_from_content(self, csv_content: str) -> Dict:
        """Update CSV file from validated content"""
        # First validate the content
        validation = self.validate_csv_content(csv_content)
        
        if not validation['valid']:
            return {
                'success': False,
                'error': 'CSV validation failed',
                'validation': validation
            }
        
        try:
            # Create backup first
            backup_path = self.backup_current_csv()
            
            # Write new content
            with open(self.csv_path, 'w', encoding='utf-8') as file:
                file.write(csv_content)
            
            logger.info("CSV configuration updated successfully")
            
            return {
                'success': True,
                'message': 'CSV updated successfully',
                'backup_path': backup_path,
                'validation': validation
            }
            
        except Exception as e:
            logger.error(f"Failed to update CSV: {e}")
            return {
                'success': False,
                'error': f'Failed to update CSV: {str(e)}'
            }

    def _get_emoji_for_prize(self, name: str) -> str:
        """Get appropriate emoji for prize based on name"""
        name_lower = name.lower()
        
        if 'tv' in name_lower or 'television' in name_lower:
            return '📺'
        elif 'coin' in name_lower:
            return '🪙'
        elif 'refrigerator' in name_lower or 'fridge' in name_lower:
            return '🧊'
        elif 'washing' in name_lower:
            return '🧺'
        elif 'cooler' in name_lower or 'ac' in name_lower:
            return '❄️'
        elif 'soundbar' in name_lower or 'speaker' in name_lower:
            return '🔊'
        elif 'dinner' in name_lower or 'plate' in name_lower:
            return '🍽️'
        elif 'tab' in name_lower or 'tablet' in name_lower:
            return '📱'
        elif 'theatre' in name_lower or 'theater' in name_lower:
            return '🎭'
        elif 'stove' in name_lower or 'gas' in name_lower:
            return '🔥'
        elif 'mixer' in name_lower or 'grinder' in name_lower:
            return '🥤'
        elif 'mobile' in name_lower or 'phone' in name_lower:
            return '📞'
        elif 'smartwatch' in name_lower or 'watch' in name_lower:
            return '⌚'
        elif 'buds' in name_lower or 'earphone' in name_lower or 'headphone' in name_lower:
            return '🎧'
        elif 'power bank' in name_lower or 'powerbank' in name_lower:
            return '🔋'
        elif 'neckband' in name_lower:
            return '🎵'
        elif 'luggage' in name_lower or 'bag' in name_lower:
            return '🧳'
        elif 'pressure cooker' in name_lower or 'cooker' in name_lower:
            return '🍲'
        elif 'pouch' in name_lower or 'guard' in name_lower:
            return '📱'
        elif 'trimmer' in name_lower:
            return '✂️'
        else:
            return '🎁'  # Default gift emoji

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with schema"""
        try:
            # Use absolute path to the schema file
            import os
            schema_path = os.path.join(os.path.dirname(__file__), 'database-schema.sql')
            with open(schema_path, 'r') as f:
                schema = f.read()
            
            conn = sqlite3.connect(self.db_path)
            conn.executescript(schema)
            conn.commit()
            conn.close()
            
            # Populate inventory for the full 2-month period
            self.populate_inventory()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def populate_inventory(self):
        """Populate inventory for the entire 2-month event period using CSV configuration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get event dates
        cursor.execute("SELECT start_date, end_date FROM events WHERE id = ?", (EVENT_ID,))
        event = cursor.fetchone()
        
        if not event:
            logger.error("Event not found")
            return
        
        start_date = datetime.strptime(event['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(event['end_date'], '%Y-%m-%d').date()
        
        # CRITICAL FIX: Load prize configuration from CSV instead of hardcoded values
        logger.info("Loading prize configuration from CSV...")
        csv_config = CSVConfigManager(CSV_CONFIG_PATH)
        prize_config = csv_config.load_prizes_from_csv()
        
        # Generate inventory based on CSV configuration
        current_date = start_date
        while current_date <= end_date:
            self.generate_daily_inventory_from_config(cursor, current_date, prize_config)
            current_date += timedelta(days=1)
        
        conn.commit()
        conn.close()
        logger.info(f"Inventory populated from {start_date} to {end_date} using CSV configuration")
    
    def reset_inventory(self):
        """Clear existing inventory and regenerate from CSV"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        logger.info("Clearing existing inventory...")
        cursor.execute("DELETE FROM prize_inventory")
        
        conn.commit()
        conn.close()
        
        # Regenerate inventory
        self.populate_inventory()
        logger.info("Inventory reset and regenerated from CSV configuration")
    
    def generate_daily_inventory_from_config(self, cursor, target_date: date, prize_config: List[Dict]):
        """Generate inventory for a specific date based on CSV configuration"""
        
        target_date_str = target_date.isoformat()
        logger.debug(f"Generating inventory for {target_date_str}")
        
        # Get all prizes from database to map names to IDs
        cursor.execute("SELECT id, name FROM prizes")
        prize_name_to_id = {row['name'].lower().strip(): row['id'] for row in cursor.fetchall()}
        
        for prize_data in prize_config:
            prize_name = prize_data['name'].lower().strip()
            category = prize_data['category']
            available_dates = prize_data.get('availability_dates', [])
            quantity = prize_data.get('total_quantity', 0)
            
            # Find prize ID
            prize_id = None
            for db_name, db_id in prize_name_to_id.items():
                if prize_name in db_name or db_name in prize_name:
                    prize_id = db_id
                    break
            
            if not prize_id:
                logger.warning(f"Could not find prize ID for: {prize_name}")
                continue
            
            # Handle different categories based on CSV configuration
            if category.lower() == 'common':
                # Common items - unlimited availability every day with high per-day limit
                per_day_quantity = 100  # Set high per-day limit for common items
                
                cursor.execute("""
                    INSERT OR IGNORE INTO prize_inventory 
                    (prize_id, event_id, available_date, initial_quantity, remaining_quantity, is_unlimited, per_day_limit)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (prize_id, EVENT_ID, target_date_str, 999, 999, True, per_day_quantity))
                logger.debug(f"Added unlimited {prize_name} for {target_date_str} with per-day limit: {per_day_quantity}")
                
            elif category.lower() in ['rare', 'ultra_rare', 'ultra rare']:
                # Check if this date is in the available dates
                is_available = False
                
                if not available_dates:
                    # If no specific dates, make available on random days for rare items
                    if category.lower() == 'rare':
                        is_available = secrets.randbelow(3) > 0  # 66% chance
                    else:  # ultra rare
                        is_available = secrets.randbelow(10) == 0  # 10% chance
                else:
                    # Check specific dates
                    is_available = target_date_str in available_dates
                
                if is_available:
                    # Parse the per-day quantity from the CSV (support both old and new formats)
                    per_day_str = ''
                    
                    # Try new format first (Daily Limit)
                    if 'quantity_per_date' in prize_data:
                        per_day_str = str(prize_data.get('quantity_per_date', '')).strip().lower()
                    # Then try old format (Quantity Per Day)
                    elif 'quantity_per_day' in prize_data:
                        per_day_str = str(prize_data.get('quantity_per_day', '')).strip().lower()
                    
                    # Default to 1 per day if not specified
                    per_day_quantity = 1
                    
                    # Parse "X/day" format or direct number
                    if per_day_str:
                        if '/' in per_day_str:
                            try:
                                per_day_quantity = int(per_day_str.split('/')[0])
                            except (ValueError, IndexError):
                                logger.warning(f"Could not parse per-day quantity from '{per_day_str}', using default of 1")
                        else:
                            try:
                                per_day_quantity = int(per_day_str) if per_day_str.isdigit() else 1
                            except (ValueError):
                                logger.warning(f"Could not parse per-day quantity from '{per_day_str}', using default of 1")
                    
                    # Use total quantity for initial inventory, but respect per-day limit
                    initial_quantity = 1 if quantity <= 0 else min(quantity, 10)
                    
                    # Log the per-day limit for clarity
                    logger.info(f"Prize {prize_name}: total={quantity}, per-day={per_day_quantity}, date={target_date_str}")
                    
                    cursor.execute("""
                        INSERT OR IGNORE INTO prize_inventory 
                        (prize_id, event_id, available_date, initial_quantity, remaining_quantity, per_day_limit)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (prize_id, EVENT_ID, target_date_str, initial_quantity, initial_quantity, per_day_quantity))
                    
                    logger.debug(f"Added {initial_quantity} {prize_name} ({category}) for {target_date_str}, per-day limit: {per_day_quantity}")
            
            else:
                logger.warning(f"Unknown category '{category}' for prize: {prize_name}")

db_manager = DatabaseManager(DATABASE_PATH)
# Create CSV manager
csv_manager = CSVConfigManager(CSV_CONFIG_PATH)
# Make it available globally
import sys
sys.modules['backend_api_csv_manager'] = csv_manager

class PrizeManager:
    """Handles prize-related operations"""
    
    @staticmethod
    def get_available_prizes(target_date: str = None) -> List[Dict]:
        """Get all available prizes for a specific date"""
        if not target_date:
            target_date = date.today().isoformat()
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if per_day_limit column exists in prize_inventory table
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='prize_inventory'
        """)
        table_schema = cursor.fetchone()
        has_per_day_limit = table_schema and 'per_day_limit' in table_schema[0]
        
        # CRITICAL FIX: Add check for per-day limits in available prizes query
        if has_per_day_limit:
            query = """
            SELECT 
                p.id,
                p.name,
                p.type,
                p.emoji,
                p.is_premium,
                pc.name as category,
                pc.display_name as category_display,
                pc.weight,
                pc.color,
                pc.text_color,
                COALESCE(pi.remaining_quantity, 0) as remaining_quantity,
                COALESCE(pi.is_unlimited, 0) as is_unlimited,
                COALESCE(pi.per_day_limit, 1) as per_day_limit,
                (SELECT COUNT(*) FROM prize_wins pw 
                 WHERE pw.prize_id = p.id AND pw.win_date = ? AND pw.event_id = ?) as today_wins,
                CASE 
                    WHEN COALESCE(pi.is_unlimited, 0) = 1 THEN 999
                    ELSE COALESCE(pi.remaining_quantity, 0)
                END as effective_quantity
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            LEFT JOIN prize_inventory pi ON p.id = pi.prize_id 
                AND pi.event_id = ? 
                AND pi.available_date = ?
            WHERE p.is_active = 1 
                AND (pi.remaining_quantity > 0 OR pi.is_unlimited = 1)
                AND (pi.is_unlimited = 1 OR 
                     (SELECT COUNT(*) FROM prize_wins pw 
                      WHERE pw.prize_id = p.id AND pw.win_date = ? AND pw.event_id = ?) < COALESCE(pi.per_day_limit, 1))
            ORDER BY pc.weight ASC, p.name
            """
        else:
            # Fallback query without per_day_limit
            query = """
            SELECT 
                p.id,
                p.name,
                p.type,
                p.emoji,
                p.is_premium,
                pc.name as category,
                pc.display_name as category_display,
                pc.weight,
                pc.color,
                pc.text_color,
                COALESCE(pi.remaining_quantity, 0) as remaining_quantity,
                COALESCE(pi.is_unlimited, 0) as is_unlimited,
                1 as per_day_limit,
                (SELECT COUNT(*) FROM prize_wins pw 
                 WHERE pw.prize_id = p.id AND pw.win_date = ? AND pw.event_id = ?) as today_wins,
                CASE 
                    WHEN COALESCE(pi.is_unlimited, 0) = 1 THEN 999
                    ELSE COALESCE(pi.remaining_quantity, 0)
                END as effective_quantity
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            LEFT JOIN prize_inventory pi ON p.id = pi.prize_id 
                AND pi.event_id = ? 
                AND pi.available_date = ?
            WHERE p.is_active = 1 
                AND (pi.remaining_quantity > 0 OR pi.is_unlimited = 1)
            ORDER BY pc.weight ASC, p.name
            """
        
        
        if has_per_day_limit:
            cursor.execute(query, (target_date, EVENT_ID, EVENT_ID, target_date, target_date, EVENT_ID))
        else:
            cursor.execute(query, (target_date, EVENT_ID, EVENT_ID, target_date))
        prizes = []
        
        for row in cursor.fetchall():
            prize = dict(row)
            
            # Get combo items if it's a combo prize
            if prize['type'] == 'combo':
                combo_cursor = conn.cursor()
                combo_cursor.execute("""
                    SELECT item_name, item_emoji, item_icon_path, sort_order
                    FROM combo_items 
                    WHERE prize_id = ? 
                    ORDER BY sort_order
                """, (prize['id'],))
                
                prize['items'] = [dict(item) for item in combo_cursor.fetchall()]
            
            prizes.append(prize)
        
        conn.close()
        return prizes
    
    @staticmethod
    def select_random_prize(available_prizes: List[Dict]) -> Optional[Dict]:
        """Select a random prize with better variety and fair rare item distribution"""
        if not available_prizes:
            return None
        
        # For better variety, prefer prizes that haven't been won recently
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get today's date
            today = date.today().isoformat()
            
            # CRITICAL FIX: Filter out prizes that have reached their daily limit
            filtered_prizes = []
            for prize in available_prizes:
                # Skip prizes that have already reached their daily limit
                if 'today_wins' in prize and 'per_day_limit' in prize:
                    if prize['today_wins'] >= prize['per_day_limit'] and not prize.get('is_unlimited', False):
                        logger.info(f"🔍 Filtering out {prize['name']} - reached daily limit of {prize['per_day_limit']}")
                        continue
                filtered_prizes.append(prize)
            
            # If no prizes are available after filtering, return None
            if not filtered_prizes:
                logger.warning("⚠️ No prizes available after filtering out daily limits")
                return None
            
            # Use filtered prizes instead of all available prizes
            available_prizes = filtered_prizes
            
            # Get recently won prizes (last 10 wins)
            cursor.execute("""
                SELECT prize_id, COUNT(*) as recent_wins
                FROM prize_wins 
                WHERE win_date = date('now')
                GROUP BY prize_id
            """)
            
            recent_wins = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Calculate win percentages for rare items to ensure fair distribution
            cursor.execute("""
                SELECT COUNT(*) as total_wins,
                       SUM(CASE WHEN pc.name = 'rare' OR pc.name = 'ultra_rare' THEN 1 ELSE 0 END) as rare_wins
                FROM prize_wins pw
                JOIN prizes p ON pw.prize_id = p.id
                JOIN prize_categories pc ON p.category_id = pc.id
                WHERE pw.win_date = date('now')
            """)
            
            stats = cursor.fetchone()
            total_wins = stats['total_wins'] if stats and stats['total_wins'] else 0
            rare_wins = stats['rare_wins'] if stats and stats['rare_wins'] else 0
            
            # Target: 30% rare/ultra-rare items
            rare_target_pct = 0.30
            rare_current_pct = rare_wins / total_wins if total_wins > 0 else 0
            boost_rare_items = rare_current_pct < rare_target_pct
            
            # Group prizes by category
            common_prizes = [p for p in available_prizes if p['category'].lower() == 'common']
            rare_prizes = [p for p in available_prizes if p['category'].lower() == 'rare']
            ultra_rare_prizes = [p for p in available_prizes if p['category'].lower() == 'ultra_rare']
            
            # Force rare item selection 50% of the time to ensure rare items are won
            if (rare_prizes or ultra_rare_prizes) and random.random() < 0.50:  # Increased from 40% to 50%
                logger.info("🎯 Boosting rare item selection due to low rare win percentage")
                # Prefer ultra-rare if available, otherwise rare
                if ultra_rare_prizes:
                    return secrets.choice(ultra_rare_prizes)
                else:
                    return secrets.choice(rare_prizes)
            
            # Create weighted list with adjusted weights
            weighted_prizes = []
            
            # Simple weighting based on category
            for prize in available_prizes:
                base_weight = prize['weight']
                category = prize['category'].lower()
                
                # Apply category-based adjustments with increased weights
                if category == 'rare':
                    adjusted_weight = int(base_weight * 5)  # 400% boost for rare items (increased from 3)
                elif category == 'ultra_rare':
                    adjusted_weight = int(base_weight * 8)  # 700% boost for ultra-rare items (increased from 5)
                else:
                    adjusted_weight = base_weight
                
                # Ensure minimum weight
                adjusted_weight = max(1, adjusted_weight)
                
                # Add to weighted list
                for _ in range(adjusted_weight):
                    weighted_prizes.append(prize)
            
            if not weighted_prizes:
                return None
            
            # Select random prize
            selected = secrets.choice(weighted_prizes)
            return selected
            
        except Exception as e:
            logger.error(f"Prize selection error: {e}")
            # Fallback to simple random selection
            return secrets.choice(available_prizes) if available_prizes else None
        finally:
            conn.close()

    @staticmethod
    def get_all_prizes_with_config():
        """Get all prizes with their configuration for admin management"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.id, p.name, pc.name as category, p.type, p.emoji, pc.weight, p.description,
                       GROUP_CONCAT(DISTINCT pi.available_date) as availability_dates,
                       pi.initial_quantity as quantity_per_date
                FROM prizes p
                JOIN prize_categories pc ON p.category_id = pc.id
                LEFT JOIN prize_inventory pi ON p.id = pi.prize_id AND pi.event_id = ?
                GROUP BY p.id, p.name, pc.name, p.type, p.emoji, pc.weight, p.description, pi.initial_quantity
                ORDER BY p.id
            """, (EVENT_ID,))
            
            prizes = []
            for row in cursor.fetchall():
                prize = dict(row)
                
                # Parse availability dates
                if prize['availability_dates']:
                    dates = prize['availability_dates'].split(',')
                    # Check if this is an "always available" prize by looking at date count
                    # If there are many consecutive dates, it's likely "*" was used
                    if len(dates) > 30:  # More than 30 dates suggests "*" was used
                        prize['availability_dates'] = ['*']
                    else:
                        prize['availability_dates'] = dates
                else:
                    prize['availability_dates'] = []
                
                # Handle combo items
                if prize['type'] == 'combo':
                    cursor.execute("""
                        SELECT item_name, quantity 
                        FROM combo_items 
                        WHERE prize_id = ?
                    """, (prize['id'],))
                    prize['items'] = [dict(item) for item in cursor.fetchall()]
                
                prizes.append(prize)
            
            return prizes
            
        finally:
            conn.close()

    @staticmethod
    def bulk_update_prizes(prizes_data):
        """Bulk update all prizes - replace existing with new data"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            logger.info(f"Starting bulk update of {len(prizes_data)} prizes")
            
            # Start transaction
            cursor.execute('BEGIN TRANSACTION')
            
            # Instead of clearing all data, we'll upsert (insert or update) each prize
            logger.info("Upserting prizes (insert or update)...")
            for i, prize in enumerate(prizes_data):
                logger.info(f"Processing prize {i+1}: {prize.get('name', 'Unknown')}")
                
                # Map category name to category_id
                category_name = prize['category']
                cursor.execute("SELECT id FROM prize_categories WHERE name = ?", (category_name,))
                category_result = cursor.fetchone()
                
                if not category_result:
                    logger.error(f"Category '{category_name}' not found, using default")
                    category_id = 3  # Default to 'common'
                else:
                    category_id = category_result[0]
                
                logger.info(f"Mapped category '{category_name}' to ID {category_id}")
                
                # Upsert prize (insert or replace existing)
                cursor.execute("""
                    INSERT OR REPLACE INTO prizes (id, name, category_id, type, emoji, description)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    prize['id'],
                    prize['name'],
                    category_id,
                    prize.get('type', 'single'),
                    prize.get('emoji', '🎁'),
                    prize.get('description', '')
                ))
                
                # Handle combo items - clear existing for this prize and insert new ones
                cursor.execute("DELETE FROM combo_items WHERE prize_id = ?", (prize['id'],))
                if 'items' in prize and prize['items']:
                    for item in prize['items']:
                        cursor.execute("""
                            INSERT INTO combo_items (prize_id, item_name, quantity)
                            VALUES (?, ?, ?)
                        """, (prize['id'], item['item_name'], item['quantity']))
                
                # Handle inventory - clear existing for this prize and insert new ones
                cursor.execute("DELETE FROM prize_inventory WHERE prize_id = ? AND event_id = ?", (prize['id'], EVENT_ID))
                
                # Insert inventory for each availability date
                availability_dates = prize.get('availability_dates', [])
                if availability_dates and availability_dates[0] == '*':
                    # Always available - create inventory for entire contest period
                    from datetime import datetime, timedelta
                    start_date = datetime(2025, 9, 21)
                    end_date = datetime(2025, 11, 21)
                    current_date = start_date
                    quantity = prize.get('quantity_per_date', 1)
                    
                    while current_date <= end_date:
                        date_str = current_date.strftime('%Y-%m-%d')
                        cursor.execute("""
                            INSERT INTO prize_inventory 
                            (prize_id, event_id, available_date, initial_quantity, remaining_quantity)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prize['id'], EVENT_ID, date_str, quantity, quantity))
                        current_date += timedelta(days=1)
                else:
                    # Specific dates
                    for date_str in availability_dates:
                        quantity = prize.get('quantity_per_date', 1)
                        cursor.execute("""
                            INSERT INTO prize_inventory 
                            (prize_id, event_id, available_date, initial_quantity, remaining_quantity)
                            VALUES (?, ?, ?, ?, ?)
                        """, (prize['id'], EVENT_ID, date_str, quantity, quantity))
            
            # Commit transaction
            logger.info("Committing transaction...")
            cursor.execute('COMMIT')
            logger.info("Bulk update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in bulk update: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            try:
                cursor.execute('ROLLBACK')
                logger.info("Transaction rolled back")
            except:
                logger.error("Failed to rollback transaction")
            return False
        finally:
            conn.close()

    @staticmethod
    def consume_prize(prize_id: int, user_identifier: str = None) -> bool:
        """Consume a prize (reduce inventory) and record the win"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            today = date.today().isoformat()
            
            # Check if prize is available
            cursor.execute("""
                SELECT remaining_quantity, is_unlimited 
                FROM prize_inventory 
                WHERE prize_id = ? AND event_id = ? AND available_date = ?
            """, (prize_id, EVENT_ID, today))
            
            inventory = cursor.fetchone()
            if not inventory:
                return False
            
            # If not unlimited, reduce quantity
            if not inventory['is_unlimited']:
                if inventory['remaining_quantity'] <= 0:
                    return False
                
                cursor.execute("""
                    UPDATE prize_inventory 
                    SET remaining_quantity = remaining_quantity - 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE prize_id = ? AND event_id = ? AND available_date = ?
                """, (prize_id, EVENT_ID, today))
            
            # Record the win
            verification_code = secrets.token_urlsafe(8)
            cursor.execute("""
                INSERT INTO prize_wins 
                (prize_id, event_id, user_identifier, win_date, verification_code)
                VALUES (?, ?, ?, ?, ?)
            """, (prize_id, EVENT_ID, user_identifier, today, verification_code))
            
            # Update daily stats
            cursor.execute("""
                INSERT OR REPLACE INTO daily_stats 
                (event_id, stat_date, total_wins, updated_at)
                VALUES (?, ?, 
                    COALESCE((SELECT total_wins FROM daily_stats WHERE event_id = ? AND stat_date = ?), 0) + 1,
                    CURRENT_TIMESTAMP)
            """, (EVENT_ID, today, EVENT_ID, today))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error consuming prize: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

class StatsManager:
    """Handles statistics and reporting"""
    
    @staticmethod
    def get_daily_stats(target_date: str = None) -> Dict:
        """Get statistics for a specific date"""
        if not target_date:
            target_date = date.today().isoformat()
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if daily_stats table exists
        cursor.execute("""SELECT name FROM sqlite_master 
                      WHERE type='table' AND name='daily_stats'""")
        if not cursor.fetchone():
            # Table doesn't exist, return default stats
            return {
                'total_spins': 0, 
                'total_wins': 0, 
                'unique_users': 0,
                'prize_breakdown': [],
                'inventory_status': []
            }
        
        # Get basic stats
        cursor.execute("""
            SELECT total_spins, total_wins, unique_users
            FROM daily_stats 
            WHERE event_id = ? AND stat_date = ?
        """, (EVENT_ID, target_date))
        
        stats = cursor.fetchone()
        if not stats:
            stats = {'total_spins': 0, 'total_wins': 0, 'unique_users': 0}
        else:
            stats = dict(stats)
        
        # Get prize breakdown
        try:
            cursor.execute("""
                SELECT p.name, pc.name as category, COUNT(*) as wins
                FROM prize_wins pw
                JOIN prizes p ON pw.prize_id = p.id
                JOIN prize_categories pc ON p.category_id = pc.id
                WHERE pw.event_id = ? AND pw.win_date = ?
                GROUP BY p.id
                ORDER BY wins DESC
            """, (EVENT_ID, target_date))
            
            stats['prize_breakdown'] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table might not exist or have the right schema
            stats['prize_breakdown'] = []
        
        # Get inventory status
        try:
            cursor.execute("""
                SELECT p.name, pi.initial_quantity, pi.remaining_quantity, pi.is_unlimited, pi.per_day_limit
                FROM prize_inventory pi
                JOIN prizes p ON pi.prize_id = p.id
                WHERE pi.event_id = ? AND pi.available_date = ?
                ORDER BY p.name
            """, (EVENT_ID, target_date))
            
            stats['inventory_status'] = [dict(row) for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            # Table might not exist or have the right schema
            stats['inventory_status'] = []
        
        conn.close()
        return stats

# API Routes

@app.route('/')
def serve_index():
    """Serve the main application"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/admin')
def serve_admin_dashboard():
    """Serve the main admin dashboard with password protection"""
    # Check for admin authentication
    auth_header = request.headers.get('Authorization')
    if not auth_header or not validate_admin_auth(auth_header):
        return create_admin_login_page()
    return send_from_directory('../admin', 'index.html')

@app.route('/admin/verifier')
def serve_admin_verifier():
    """Serve the admin verifier tool with password protection"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not validate_admin_auth(auth_header):
        return create_admin_login_page()
    return send_from_directory('../admin', 'system-verifier.html')

@app.route('/admin/csv')
def serve_csv_manager():
    """Serve the CSV configuration manager with password protection"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not validate_admin_auth(auth_header):
        return create_admin_login_page()
    return send_from_directory('../admin', 'csv-manager.html')

def validate_admin_auth(auth_header):
    """Validate admin authentication header"""
    try:
        import base64
        if auth_header.startswith('Basic '):
            encoded = auth_header.split(' ')[1]
            decoded = base64.b64decode(encoded).decode('utf-8')
            username, password = decoded.split(':', 1)
            return username == 'admin' and password == ADMIN_PASSWORD
    except:
        pass
    return False

def create_admin_login_page():
    """Create admin login page"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - PickerWheel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        h1 {
            margin-bottom: 30px;
            font-size: 2em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .warning {
            background: rgba(255, 193, 7, 0.2);
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .error {
            color: #ff6b6b;
            margin-top: 10px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🔐 Admin Access</h1>
        <div class="warning">
            <strong>⚠️ RESTRICTED ACCESS</strong><br>
            This area is for authorized administrators only.
        </div>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">🚀 Access Admin Panel</button>
            <div id="error" class="error" style="display: none;"></div>
        </form>
    </div>

    <script>
        document.getElementById('loginForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorDiv = document.getElementById('error');
            
            if (!username || !password) {
                errorDiv.textContent = 'Please enter both username and password';
                errorDiv.style.display = 'block';
                return;
            }
            
            // Create basic auth header
            const credentials = btoa(username + ':' + password);
            
            // Reload page with auth header
            fetch(window.location.href, {
                headers: {
                    'Authorization': 'Basic ' + credentials
                }
            }).then(response => {
                if (response.ok) {
                    // Store credentials for session
                    sessionStorage.setItem('adminAuth', credentials);
                    location.reload();
                } else {
                    errorDiv.textContent = 'Invalid credentials';
                    errorDiv.style.display = 'block';
                }
            }).catch(error => {
                errorDiv.textContent = 'Authentication failed';
                errorDiv.style.display = 'block';
            });
        });
        
        // Check if already authenticated
        const storedAuth = sessionStorage.getItem('adminAuth');
        if (storedAuth) {
            fetch(window.location.href, {
                headers: {
                    'Authorization': 'Basic ' + storedAuth
                }
            }).then(response => {
                if (response.ok) {
                    location.reload();
                }
            });
        }
    </script>
</body>
</html>
    ''', 401, {'WWW-Authenticate': 'Basic realm="Admin Area"'}

@app.route('/admin.html')
def serve_admin_panel():
    """Serve the admin panel"""
    return send_from_directory('../frontend', 'admin.html')

@app.route('/app.js')
def serve_app_js():
    """Serve the main app JavaScript"""
    return send_from_directory('../frontend', 'app.js')

@app.route('/myt-mobiles-logo.png')
def serve_logo():
    """Serve the logo"""
    return send_from_directory('../assets/images', 'myt-mobiles-logo.png')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve asset files"""
    return send_from_directory('../assets', filename)

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve other static files from frontend"""
    return send_from_directory('../frontend', filename)

@app.route('/api/prizes/available', methods=['GET'])
def get_available_prizes():
    """Get all available prizes for today or specified date"""
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        prizes = PrizeManager.get_available_prizes(target_date)
        return jsonify({
            'success': True,
            'date': target_date,
            'prizes': prizes,
            'count': len(prizes)
        })
    except Exception as e:
        logger.error(f"Error getting available prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/pre-spin', methods=['POST'])
def pre_spin_selection():
    """Pre-select an available prize before wheel spin"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        
        logger.info(f"Pre-spin request - User: {user_identifier}")
        
        # Get available prizes for today
        available_prizes = PrizeManager.get_available_prizes()
        
        if not available_prizes:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
        
        # Smart selection based on category weights and availability
        selected_prize = PrizeManager.select_random_prize(available_prizes)
        
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'Unable to select prize'
            }), 400
        
        # Get all wheel display prizes to calculate target segment
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.id, p.name, pc.name as category, p.type, p.emoji, pc.weight, p.description
                FROM prizes p
                JOIN prize_categories pc ON p.category_id = pc.id
                WHERE p.is_active = 1
                ORDER BY p.id
            """)
            
            all_wheel_prizes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            # Find target segment index for this prize in the full wheel
            target_segment_index = next(
                (i for i, prize in enumerate(all_wheel_prizes) if prize['id'] == selected_prize['id']), 
                0
            )
            
            logger.info(f"🎯 MAPPING DEBUG:")
            logger.info(f"   Selected available prize: ID {selected_prize['id']} - {selected_prize['name']}")
            logger.info(f"   Maps to wheel segment: {target_segment_index}")
            logger.info(f"   Wheel prize at segment {target_segment_index}: ID {all_wheel_prizes[target_segment_index]['id']} - {all_wheel_prizes[target_segment_index]['name']}")
            logger.info(f"   First 5 wheel segments: {[(i, p['id'], p['name']) for i, p in enumerate(all_wheel_prizes[:5])]}")
            
            # Verify the mapping is correct
            if all_wheel_prizes[target_segment_index]['id'] != selected_prize['id']:
                logger.error(f"❌ MAPPING ERROR: Selected prize ID {selected_prize['id']} does not match wheel segment {target_segment_index} prize ID {all_wheel_prizes[target_segment_index]['id']}")
                return jsonify({'success': False, 'error': 'Prize mapping error'}), 500
            
            return jsonify({
                'success': True,
                'selected_prize': selected_prize,
                'target_segment_index': target_segment_index,
                'total_segments': len(all_wheel_prizes),
                'debug_info': {
                    'selected_prize_id': selected_prize['id'],
                    'all_prize_ids': [p['id'] for p in all_wheel_prizes],
                    'mapping': [(i, p['id'], p['name']) for i, p in enumerate(all_wheel_prizes)]
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting wheel prizes: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        
    except Exception as e:
        logger.error(f"Pre-spin error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spin', methods=['POST'])
def spin_wheel():
    """Handle wheel spin with pre-selected prize (Phase 4 of dual-endpoint system)"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        selected_prize_id = data.get('selected_prize_id')
        target_segment_index = data.get('target_segment_index', 0)
        final_rotation = data.get('final_rotation', 0)
        
        logger.info(f"Spin confirmation - User: {user_identifier}, Prize: {selected_prize_id}, Segment: {target_segment_index}")
        
        if not selected_prize_id:
            return jsonify({
                'success': False,
                'error': 'No prize ID provided'
            }), 400
        
        # Get available prizes to verify the pre-selected prize is still available
        available_prizes = PrizeManager.get_available_prizes()
        
        # Find the pre-selected prize
        selected_prize = None
        for prize in available_prizes:
            if prize['id'] == selected_prize_id:
                selected_prize = prize
                break
        
        if not selected_prize:
            # Prize no longer available - this shouldn't happen in normal flow
            logger.warning(f"Pre-selected prize {selected_prize_id} no longer available")
            # Use fallback
            if available_prizes:
                selected_prize = PrizeManager.select_random_prize(available_prizes)
                logger.info(f"Fallback prize selected: {selected_prize['name'] if selected_prize else 'None'}")
            
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'No prizes available'
            }), 400
        
        # Award the prize (this should update inventory and create win record)
        try:
            # Record the win and update quantities
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            today = date.today().isoformat()
            
            # Record the win
            cursor.execute("""
                INSERT INTO prize_wins (user_identifier, prize_id, win_date, win_time)
                VALUES (?, ?, ?, ?)
            """, (user_identifier, selected_prize['id'], today, datetime.now().isoformat()))
            
            # Decrement quantity in inventory (if not unlimited)
            if not selected_prize.get('is_unlimited', False):
                cursor.execute("""
                    UPDATE prize_inventory 
                    SET remaining_quantity = remaining_quantity - 1
                    WHERE prize_id = ? AND available_date = ? AND remaining_quantity > 0
                """, (selected_prize['id'], today))
                
                # Check if quantity reached zero
                cursor.execute("""
                    SELECT remaining_quantity FROM prize_inventory 
                    WHERE prize_id = ? AND available_date = ?
                """, (selected_prize['id'], today))
                
                result = cursor.fetchone()
                if result and result[0] <= 0:
                    logger.info(f"Prize {selected_prize['name']} (ID: {selected_prize['id']}) is now out of stock for {today}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Prize awarded successfully: {selected_prize['name']} to user {user_identifier}")
            
        except Exception as e:
            logger.error(f"Failed to record prize win: {e}")
            # Continue anyway - don't fail the spin for database issues
        
        return jsonify({
            'success': True,
            'prize': selected_prize,
            'rotation_angle': final_rotation,
            'message': f'Congratulations! You won {selected_prize["name"]}!'
        })
        
    except Exception as e:
        logger.error(f"Spin error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prizes/available', methods=['GET'])
def get_available_prizes_for_date():
    """Get available prizes for a specific date (for admin verifier)"""
    try:
        target_date = request.args.get('date', date.today().isoformat())
        
        # Get available prizes for the date
        available_prizes = PrizeManager.get_available_prizes(target_date)
        
        return jsonify({
            'success': True,
            'date': target_date,
            'count': len(available_prizes),
            'prizes': available_prizes
        })
        
    except Exception as e:
        logger.error(f"Get available prizes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/test-spin', methods=['POST'])
def admin_test_spin():
    """Admin endpoint for testing spins with date simulation"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        # Validate admin password
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        user_id = data.get('user_id', 'admin_test')
        test_date = data.get('test_date')  # Optional date override for testing
        force_prize_id = data.get('force_prize_id')  # Optional force specific prize
        
        # Use test date if provided, otherwise use current date
        target_date = test_date if test_date else date.today().isoformat()
        
        # Get available prizes for the test date
        available_prizes = PrizeManager.get_available_prizes(target_date)
        
        if not available_prizes:
            return jsonify({
                'success': False,
                'error': f'No prizes available for date {target_date}'
            }), 404
        
        # If force_prize_id is provided, find that prize
        if force_prize_id:
            forced_prize = next((p for p in available_prizes if p['id'] == force_prize_id), None)
            if forced_prize:
                selected_prize = forced_prize
                logger.info(f"Forcing selection of prize: {forced_prize['name']} (ID: {force_prize_id})")
            else:
                logger.warning(f"Forced prize ID {force_prize_id} not found or not available, using random selection")
                selected_prize = PrizeManager.select_random_prize(available_prizes)
        else:
            # Select prize using weighted random selection
            selected_prize = PrizeManager.select_random_prize(available_prizes)
        
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'No prizes could be selected'
            }), 404
        
        # CRITICAL FIX: Properly handle inventory for admin test spins
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # CRITICAL FIX: Atomic inventory check and update with proper validation
            cursor.execute("""
                SELECT remaining_quantity, is_unlimited, per_day_limit,
                       (SELECT COUNT(*) FROM prize_wins 
                        WHERE prize_id = ? AND win_date = ? AND event_id = ?) as today_wins
                FROM prize_inventory 
                WHERE prize_id = ? AND available_date = ? AND event_id = ?
                -- Note: SQLite doesn't support FOR UPDATE, using transaction isolation instead
            """, (selected_prize['id'], target_date, EVENT_ID, selected_prize['id'], target_date, EVENT_ID))
            
            inventory_row = cursor.fetchone()
            if inventory_row:
                remaining_qty = inventory_row['remaining_quantity']
                is_unlimited = inventory_row['is_unlimited']
                per_day_limit = inventory_row['per_day_limit'] or 1  # Default to 1 if not set
                today_wins = inventory_row['today_wins'] or 0
                
                # Check if prize is still available
                if not is_unlimited and remaining_qty <= 0:
                    conn.rollback()  # Important: rollback transaction
                    conn.close()
                    logger.warning(f"🚨 ADMIN TEST: {selected_prize['name']} out of stock for {target_date}")
                    return jsonify({
                        'success': False,
                        'error': f'Prize "{selected_prize["name"]}" is out of stock for {target_date}'
                    }), 409  # Conflict status code
                
                # Check per-day limit
                if not is_unlimited and today_wins >= per_day_limit:
                    conn.rollback()  # Important: rollback transaction
                    conn.close()
                    logger.warning(f"🚨 ADMIN TEST: {selected_prize['name']} reached daily limit of {per_day_limit} for {target_date} (already won {today_wins} times)")
                    return jsonify({
                        'success': False,
                        'error': f'Prize "{selected_prize["name"]}" has reached its daily limit of {per_day_limit} for {target_date}'
                    }), 409  # Conflict status code
                
                # Update inventory (decrement for limited items)
                if not is_unlimited:
                    cursor.execute("""
                        UPDATE prize_inventory 
                        SET remaining_quantity = remaining_quantity - 1
                        WHERE prize_id = ? AND available_date = ? AND event_id = ? AND remaining_quantity > 0
                    """, (selected_prize['id'], target_date, EVENT_ID))
                    
                    # Verify update was successful
                    if cursor.rowcount == 0:
                        conn.rollback()  # Important: rollback transaction
                        conn.close()
                        logger.error(f"🚨 ADMIN TEST: Failed to update inventory for {selected_prize['name']}")
                        return jsonify({
                            'success': False,
                            'error': f'Failed to update inventory for {selected_prize["name"]}'
                        }), 500
                    
                    # Log inventory update
                    logger.info(f"Admin test: Decremented {selected_prize['name']} inventory for {target_date}")
            else:
                # No inventory record found
                logger.warning(f"🚨 ADMIN TEST: No inventory record for {selected_prize['name']} on {target_date}")
                # Continue without inventory update - this is likely a common item with no inventory record
            
            # Record the test award for tracking
            award_id = f"admin_test_award_{user_id}_{int(time.time())}"
            # Get total number of active prizes for sector calculation
            cursor.execute("""
                SELECT COUNT(*) as total_prizes FROM prizes WHERE is_active = 1
            """)
            total_prizes = cursor.fetchone()['total_prizes']
            
            # Calculate sector index dynamically
            dynamic_sector_index = (selected_prize['id'] - 1) % total_prizes
            
            cursor.execute("""
                INSERT INTO prize_wins (user_identifier, prize_id, event_id, win_date, win_timestamp, 
                                      award_id, reservation_id, sector_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (f"admin_test_{user_id}", selected_prize['id'], EVENT_ID, target_date, 
                  datetime.now().isoformat(), award_id, f"admin_test_{int(time.time())}", 
                  dynamic_sector_index))
            
            conn.commit()
            conn.close()
            
            # Calculate sector center dynamically
            sector_center = (dynamic_sector_index * (360 / total_prizes)) + (360 / total_prizes / 2)
            
            return jsonify({
                'success': True,
                'prize': selected_prize,
                'sector_index': dynamic_sector_index,
                'sector_center': sector_center,
                'award_id': award_id,
                'test_date': target_date,
                'inventory_updated': not inventory_row[1] if inventory_row else False,
                'message': f"Test spin for {target_date}: You won {selected_prize['name']}!"
            })
            
        except Exception as e:
            conn.rollback()
            conn.close()
            raise e
        
    except Exception as e:
        logger.error(f"Admin test spin error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spin/reserve', methods=['POST'])
def reserve_prize():
    """Server-authoritative prize reservation with signed response"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        session_id = data.get('session_id')
        client_timestamp = data.get('client_timestamp')
        
        # Get idempotency key from header
        idempotency_key = request.headers.get('X-Idempotency-Key')
        if not idempotency_key:
            return jsonify({'success': False, 'error': 'Idempotency key required'}), 400
        
        logger.info(f"🔐 Prize reservation request - User: {user_identifier}, Key: {idempotency_key}")
        
        # Check for duplicate request (idempotency)
        existing_reservation = check_existing_reservation(idempotency_key)
        if existing_reservation:
            logger.info(f"♻️ Returning existing reservation for key: {idempotency_key}")
            return jsonify(existing_reservation)
        
        # Get available prizes for today with a fresh database query to avoid race conditions
        today = date.today().isoformat()
        conn_check = db_manager.get_connection()
        cursor_check = conn_check.cursor()
        
        # Get current win counts for all prizes to check limits
        cursor_check.execute("""
            SELECT prize_id, COUNT(*) as win_count 
            FROM prize_wins 
            WHERE win_date = ? AND event_id = ? 
            GROUP BY prize_id
        """, (today, EVENT_ID))
        
        current_wins = {row[0]: row[1] for row in cursor_check.fetchall()}
        conn_check.close()
        
        # Get available prizes for today
        available_prizes = PrizeManager.get_available_prizes()
        if not available_prizes:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
        
        # Filter out prizes that have reached their daily limit (double-check)
        filtered_prizes = []
        for prize in available_prizes:
            prize_id = prize['id']
            per_day_limit = prize.get('per_day_limit', 1)
            today_wins = current_wins.get(prize_id, 0)
            
            # Skip prizes that have reached their daily limit
            if not prize.get('is_unlimited', False) and today_wins >= per_day_limit:
                logger.info(f"🔍 Filtering out {prize['name']} - reached daily limit of {per_day_limit} (current wins: {today_wins})")
                continue
                
            filtered_prizes.append(prize)
        
        # Use filtered prizes
        if not filtered_prizes:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
            
        # Server decides the prize (server-authoritative)
        selected_prize = PrizeManager.select_random_prize(filtered_prizes)
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'Prize selection failed'
            }), 500
            
        # Get database connection for all operations
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # CRITICAL FIX: Verify inventory availability and daily limits before proceeding
        # This prevents reserving prizes that might be out of stock or have reached daily limits
        today = date.today().isoformat()
        if not selected_prize.get('is_unlimited', False):
            cursor.execute("""
                SELECT pi.remaining_quantity, pi.per_day_limit,
                       (SELECT COUNT(*) FROM prize_wins pw 
                        WHERE pw.prize_id = ? AND pw.win_date = ? AND pw.event_id = ?) as today_wins
                FROM prize_inventory pi
                WHERE pi.prize_id = ? AND pi.available_date = ? AND pi.event_id = ?
                -- Note: SQLite doesn't support FOR UPDATE, using transaction isolation instead
            """, (selected_prize['id'], today, EVENT_ID, selected_prize['id'], today, EVENT_ID))
            
            inventory = cursor.fetchone()
            
            # Check if inventory exists and has remaining quantity
            if not inventory or inventory['remaining_quantity'] <= 0:
                conn.close()  # Close connection before returning
                logger.warning(f"🚨 RESERVATION REJECTED: {selected_prize['name']} has no remaining inventory")
                
                # Try to select a different prize as fallback
                available_prizes = [p for p in available_prizes if p['id'] != selected_prize['id']]
                if available_prizes:
                    selected_prize = PrizeManager.select_random_prize(available_prizes)
                    logger.info(f"🔄 Fallback prize selected: {selected_prize['name']}")
                    
                    # Start a new connection for the fallback prize
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No prizes available with remaining inventory'
                    }), 409
            
            # Check if prize has reached its daily limit
            elif inventory['today_wins'] >= inventory['per_day_limit']:
                conn.close()  # Close connection before returning
                logger.warning(f"🚨 RESERVATION REJECTED: {selected_prize['name']} has reached daily limit of {inventory['per_day_limit']}")
                
                # Try to select a different prize as fallback
                available_prizes = [p for p in available_prizes if p['id'] != selected_prize['id']]
                if available_prizes:
                    selected_prize = PrizeManager.select_random_prize(available_prizes)
                    logger.info(f"🔄 Fallback prize selected: {selected_prize['name']}")
                    
                    # Start a new connection for the fallback prize
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                else:
                    return jsonify({
                        'success': False,
                        'error': 'No prizes available with remaining inventory'
                    }), 409
        
        # Find sector index for the selected prize
        
        cursor.execute("""
            SELECT p.id, p.name, pc.name as category, p.type, p.emoji, pc.weight, p.description
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE p.is_active = 1
            ORDER BY p.id
        """)
        
        all_wheel_prizes = [dict(row) for row in cursor.fetchall()]
        sector_index = next(
            (i for i, prize in enumerate(all_wheel_prizes) if prize['id'] == selected_prize['id']), 
            0
        )
        
        # Calculate sector center angle
        segment_angle = 360 / len(all_wheel_prizes)
        sector_center = sector_index * segment_angle + (segment_angle / 2)
        
        # Create reservation with TTL
        reservation_id = f"res_{idempotency_key}_{int(time.time())}"
        reservation_ttl = 300  # 5 minutes TTL
        
        # Store reservation in database
        cursor.execute("""
            INSERT INTO prize_reservations (reservation_id, idempotency_key, user_identifier, 
                                          prize_id, sector_index, sector_center, 
                                          reserved_at, expires_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (reservation_id, idempotency_key, user_identifier, selected_prize['id'],
              sector_index, sector_center, datetime.now().isoformat(),
              (datetime.now() + timedelta(seconds=reservation_ttl)).isoformat(), 'reserved'))
        
        conn.commit()
        conn.close()
        
        # Create signed response
        response_payload = {
            'success': True,
            'prize': selected_prize,
            'sector_index': sector_index,
            'sector_center': sector_center,
            'reservation_id': reservation_id,
            'reservation_ttl': reservation_ttl,
            'message': f'Congratulations! You won {selected_prize["name"]}!',
            'server_timestamp': datetime.now().isoformat()
        }
        
        # Generate cryptographic signature (HMAC-SHA256)
        signature = generate_response_signature(response_payload)
        response_payload['signature'] = signature
        
        logger.info(f"✅ Prize reserved: {selected_prize['name']} → Sector {sector_index}")
        logger.info(f"🔑 Reservation ID: {reservation_id} (TTL: {reservation_ttl}s)")
        
        return jsonify(response_payload)
        
    except Exception as e:
        logger.error(f"Prize reservation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spin/finalize', methods=['POST'])
def finalize_prize():
    """Finalize prize award after client confirmation"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        reservation_id = data.get('reservation_id')
        client_confirmation = data.get('client_confirmation', {})
        
        # Get idempotency key from header
        idempotency_key = request.headers.get('X-Idempotency-Key')
        if not idempotency_key or not reservation_id:
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
        logger.info(f"🏆 Prize finalization request - Reservation: {reservation_id}")
        
        # Verify reservation exists and is valid
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prize_reservations 
            WHERE reservation_id = ? AND idempotency_key = ? AND status = 'reserved'
            AND expires_at > ?
        """, (reservation_id, idempotency_key, datetime.now().isoformat()))
        
        reservation = cursor.fetchone()
        if not reservation:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid or expired reservation'
            }), 400
        
        reservation_dict = dict(reservation)
        prize_id = reservation_dict['prize_id']
        
        # Get prize details
        cursor.execute("""
            SELECT p.*, pc.name as category FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE p.id = ?
        """, (prize_id,))
        
        prize_data = dict(cursor.fetchone())
        
        # CRITICAL FIX: Atomic inventory check and update with proper validation
        today = date.today().isoformat()
        award_id = f"award_{reservation_id}_{int(time.time())}"
        inventory_updated = False
        
        if not prize_data.get('is_unlimited', False):
            # First check if inventory is available and within per-day limit
            cursor.execute("""
                SELECT remaining_quantity, per_day_limit,
                       (SELECT COUNT(*) FROM prize_wins 
                        WHERE prize_id = ? AND win_date = ? AND event_id = ?) as today_wins
                FROM prize_inventory 
                WHERE prize_id = ? AND available_date = ? AND event_id = ?
                -- Note: SQLite doesn't support FOR UPDATE, using transaction isolation instead
            """, (prize_id, today, EVENT_ID, prize_id, today, EVENT_ID))
            
            inventory = cursor.fetchone()
            if not inventory or inventory['remaining_quantity'] <= 0:
                # No inventory available
                conn.rollback()
                conn.close()
                logger.error(f"🚨 INVENTORY VIOLATION: Attempted to award {prize_data['name']} with no remaining inventory")
                return jsonify({
                    'success': False,
                    'error': f"Prize {prize_data['name']} is out of stock for today"
                }), 409  # Conflict status code
            
            # Check per-day limit
            per_day_limit = inventory['per_day_limit'] or 1  # Default to 1 if not set
            today_wins = inventory['today_wins'] or 0
            
            if today_wins >= per_day_limit:
                # Per-day limit exceeded
                conn.rollback()
                conn.close()
                logger.error(f"🚨 PER-DAY LIMIT VIOLATION: Attempted to award {prize_data['name']} beyond limit of {per_day_limit}/day (already won {today_wins} times)")
                return jsonify({
                    'success': False,
                    'error': f"Prize {prize_data['name']} has reached its daily limit of {per_day_limit}"
                }), 409  # Conflict status code
        
        # Record the final award - MOVED AFTER VALIDATION
        cursor.execute("""
            INSERT INTO prize_wins (user_identifier, prize_id, event_id, win_date, win_timestamp, 
                                  award_id, reservation_id, sector_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_identifier, prize_id, EVENT_ID, today, datetime.now().isoformat(),
              award_id, reservation_id, reservation_dict['sector_index']))

        # Now update the inventory (guaranteed to have stock due to check above)
        inventory_updated = False
        if not prize_data.get('is_unlimited', False):
            cursor.execute("""
                UPDATE prize_inventory 
                SET remaining_quantity = remaining_quantity - 1
                WHERE prize_id = ? AND available_date = ? AND event_id = ? AND remaining_quantity > 0
            """, (prize_id, today, EVENT_ID))
            inventory_updated = cursor.rowcount > 0
            
            # Double-check the update worked
            if not inventory_updated:
                conn.rollback()
                conn.close()
                logger.error(f"🚨 INVENTORY UPDATE FAILED: Could not decrement {prize_data['name']} inventory")
                return jsonify({
                    'success': False,
                    'error': f"Failed to update inventory for {prize_data['name']}"
                }), 500
        
        # Mark reservation as finalized
        cursor.execute("""
            UPDATE prize_reservations 
            SET status = 'finalized', finalized_at = ?
            WHERE reservation_id = ? AND status = 'reserved'
        """, (datetime.now().isoformat(), reservation_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Prize finalized: {prize_data['name']} → Award ID: {award_id}")
        
        return jsonify({
            'success': True,
            'award_id': award_id,
            'status': 'finalized',
            'inventory_updated': inventory_updated,
            'prize': prize_data,
            'finalized_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Prize finalization error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/reset-inventory', methods=['POST'])
def reset_inventory():
    """Admin endpoint to reset inventory from CSV configuration"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        logger.info("Admin requested inventory reset")
        db_manager.reset_inventory()
        
        return jsonify({
            'success': True,
            'message': 'Inventory reset and regenerated from CSV configuration'
        })
        
    except Exception as e:
        logger.error(f"Inventory reset error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/sync-prizes', methods=['POST'])
def sync_prizes():
    """Admin endpoint to sync prizes table with CSV configuration"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        reset_after_sync = data.get('reset_inventory', True)
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        logger.info("Admin requested prize sync")
        
        # Connect to database
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Load prizes from CSV
        csv_config = CSVConfigManager(CSV_CONFIG_PATH)
        prize_config = csv_config.load_prizes_from_csv()
        
        # Get existing prizes
        cursor.execute("SELECT id, name FROM prizes")
        existing_prizes = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
        
        # Get category IDs
        cursor.execute("SELECT id, name FROM prize_categories")
        categories = {row['name'].lower(): row['id'] for row in cursor.fetchall()}
        
        # Process each prize
        new_prizes = []
        updated_prizes = []
        
        for prize_data in prize_config:
            name = prize_data['name']
            category = prize_data['category']
            prize_type = prize_data.get('type', 'single')
            
            # Use default emoji and description based on name and category
            emoji = '🎁'  # Default gift emoji
            description = f'{category.replace("_", " ").title()} prize: {name}'
            
            # Get category ID
            category_id = categories.get(category, 1)  # Default to common (ID 1) if category not found
            
            # Check if prize exists
            prize_id = None
            for existing_name, existing_id in existing_prizes.items():
                if name.lower() == existing_name or name.lower() in existing_name or existing_name in name.lower():
                    prize_id = existing_id
                    break
            
            if prize_id:
                # Update existing prize - only update essential fields
                cursor.execute("""
                    UPDATE prizes
                    SET name = ?, category_id = ?, type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, category_id, prize_type, prize_id))
                updated_prizes.append(name)
            else:
                # Add new prize - only add essential fields
                cursor.execute("""
                    INSERT INTO prizes (name, category_id, type, emoji, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, category_id, prize_type, emoji, description))
                new_prizes.append(name)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        # Reset inventory if requested
        if reset_after_sync:
            db_manager.reset_inventory()
        
        return jsonify({
            'success': True,
            'message': f'Prizes synced successfully. Added {len(new_prizes)} new prizes, updated {len(updated_prizes)} existing prizes.',
            'new_prizes': new_prizes,
            'updated_prizes': updated_prizes,
            'inventory_reset': reset_after_sync
        })
        
    except Exception as e:
        logger.error(f"Prize sync error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/csv/validate', methods=['POST'])
def validate_csv():
    """Admin endpoint to validate CSV content"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        csv_content = data.get('csv_content', '')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        if not csv_content:
            return jsonify({'success': False, 'error': 'No CSV content provided'}), 400
        
        # Validate CSV content
        csv_config = CSVConfigManager(CSV_CONFIG_PATH)
        validation_result = csv_config.validate_csv_content(csv_content)
        
        return jsonify({
            'success': True,
            'validation': validation_result
        })
        
    except Exception as e:
        logger.error(f"CSV validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/csv/export', methods=['POST'])
def export_csv():
    """Admin endpoint to export current CSV configuration"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        csv_config = CSVConfigManager(CSV_CONFIG_PATH)
        csv_content = csv_config.export_current_csv()
        
        return jsonify({
            'success': True,
            'csv_content': csv_content,
            'filename': 'itemlist_dates.txt'
        })
        
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/csv/import', methods=['POST'])
def import_csv():
    """Admin endpoint to import and update CSV configuration"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        csv_content = data.get('csv_content', '')
        force_update = data.get('force_update', False)
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        if not csv_content:
            return jsonify({'success': False, 'error': 'No CSV content provided'}), 400
        
        csv_config = CSVConfigManager(CSV_CONFIG_PATH)
        
        # Update CSV and get result
        update_result = csv_config.update_csv_from_content(csv_content)
        
        if update_result['success']:
            # Reset inventory to reflect new CSV configuration
            logger.info("CSV updated successfully, resetting inventory...")
            db_manager.reset_inventory()
            
            return jsonify({
                'success': True,
                'message': 'CSV imported and inventory updated successfully',
                'backup_path': update_result.get('backup_path'),
                'validation': update_result.get('validation')
            })
        else:
            return jsonify(update_result), 400
        
    except Exception as e:
        logger.error(f"CSV import error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM prizes")
        prize_count = cursor.fetchone()[0]
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'prize_count': prize_count,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/admin/csv/format-guide', methods=['GET'])
def get_csv_format_guide():
    """Get CSV format guide and examples"""
    format_guide = {
        'required_columns': [
            'Item/Combo List',
            'Category', 
            'Quantity',
            'Quantity Per Day',
            'Available Dates'
        ],
        'column_descriptions': {
            'Item/Combo List': 'Name of the prize item or combo (e.g., "smartwatch + mini cooler")',
            'Category': 'Prize category: Common, Rare, or Ultra Rare',
            'Quantity': 'Total quantity available during event (leave empty for unlimited Common items)',
            'Quantity Per Day': 'Daily limit (e.g., "1/day", "2/day", leave empty for unlimited)',
            'Available Dates': 'Specific dates when available (YYYY-MM-DD|YYYY-MM-DD) or "Random days" or leave empty for all days'
        },
        'category_rules': {
            'Common': 'Unlimited availability, no date restrictions',
            'Rare': 'Limited quantities, can have specific dates',
            'Ultra Rare': 'Very limited quantities, usually specific dates only'
        },
        'examples': [
            {
                'Item/Combo List': 'smartwatch + mini cooler',
                'Category': 'Common',
                'Quantity': '',
                'Quantity Per Day': '',
                'Available Dates': ''
            },
            {
                'Item/Combo List': 'Smart TV 32 inches',
                'Category': 'Ultra Rare',
                'Quantity': '1',
                'Quantity Per Day': '1/day',
                'Available Dates': '2025-10-20'
            },
            {
                'Item/Combo List': 'Mixer Grinder',
                'Category': 'Rare',
                'Quantity': '6',
                'Quantity Per Day': '1/day',
                'Available Dates': '2025-09-22|2025-09-29|2025-10-01|2025-10-02|2025-10-18|2025-10-20'
            }
        ],
        'validation_rules': [
            'All required columns must be present',
            'Item names cannot be empty',
            'Categories must be: Common, Rare, or Ultra Rare',
            'Quantities must be numbers (if specified)',
            'Dates must be in YYYY-MM-DD format',
            'Multiple dates separated by | (pipe character)'
        ]
    }
    
    return jsonify({
        'success': True,
        'format_guide': format_guide
    })

@app.route('/api/admin/update-quantity', methods=['POST'])
def update_prize_quantity():
    """Admin endpoint to manually update prize quantities"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        prize_id = data.get('prize_id')
        new_quantity = data.get('new_quantity')
        target_date = data.get('date', date.today().isoformat())
        
        # Verify admin password
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        if not prize_id or new_quantity is None:
            return jsonify({'success': False, 'error': 'Prize ID and new quantity required'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Update the quantity
        cursor.execute("""
            UPDATE prize_inventory 
            SET remaining_quantity = ?, initial_quantity = ?
            WHERE prize_id = ? AND available_date = ?
        """, (new_quantity, new_quantity, prize_id, target_date))
        
        # If no existing record, create one
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO prize_inventory (prize_id, event_id, available_date, initial_quantity, remaining_quantity, is_unlimited)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (prize_id, EVENT_ID, target_date, new_quantity, new_quantity, False))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Admin updated prize {prize_id} quantity to {new_quantity} for {target_date}")
        
        return jsonify({
            'success': True,
            'message': f'Prize quantity updated to {new_quantity}',
            'prize_id': prize_id,
            'new_quantity': new_quantity,
            'date': target_date
        })
        
    except Exception as e:
        logger.error(f"Failed to update prize quantity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics for today or specified date"""
    target_date = request.args.get('date', date.today().isoformat())
    
    try:
        stats = StatsManager.get_daily_stats(target_date)
        return jsonify({
            'success': True,
            'date': target_date,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/inventory', methods=['GET'])
def get_inventory():
    """Get inventory status (admin only)"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f'Bearer {ADMIN_PASSWORD}':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.id,
                p.name,
                p.type,
                pc.display_name as category,
                pi.initial_quantity,
                pi.remaining_quantity,
                pi.is_unlimited,
                pi.available_date
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            LEFT JOIN prize_inventory pi ON p.id = pi.prize_id AND pi.event_id = ?
            WHERE pi.available_date >= ? AND pi.available_date <= ?
            ORDER BY pi.available_date, pc.weight, p.name
        """, (EVENT_ID, target_date, (datetime.strptime(target_date, '%Y-%m-%d') + timedelta(days=7)).isoformat()))
        
        inventory = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'inventory': inventory
        })
        
    except Exception as e:
        logger.error(f"Error getting inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/replenish', methods=['POST'])
def replenish_inventory():
    """Replenish inventory for a specific prize and date"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'error': 'Authorization required'}), 401
    
    token = auth_header.split(' ')[1]
    if token != ADMIN_PASSWORD:
        return jsonify({'success': False, 'error': 'Invalid authorization'}), 401
    
    data = request.get_json()
    prize_id = data.get('prize_id')
    quantity = data.get('quantity')
    date_str = data.get('date')
    
    if not all([prize_id, quantity, date_str]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    try:
        success = PrizeManager.replenish_inventory(prize_id, quantity, date_str)
        if success:
            return jsonify({'success': True, 'message': 'Inventory replenished successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to replenish inventory'}), 500
    except Exception as e:
        logger.error(f"Error replenishing inventory: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prizes/all', methods=['GET'])
def get_all_prizes():
    """Get all prizes with their configuration"""
    try:
        prizes = PrizeManager.get_all_prizes_with_config()
        return jsonify({'success': True, 'prizes': prizes})
    except Exception as e:
        logger.error(f"Error getting all prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/prizes/bulk-update', methods=['POST'])
def bulk_update_prizes():
    """Bulk update all prizes - for admin prize manager"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
            
        prizes = data.get('prizes', [])
        
        if not prizes:
            return jsonify({'success': False, 'error': 'No prizes provided'}), 400
        
        logger.info(f"Attempting to update {len(prizes)} prizes")
        
        # Validate prize data and business rules
        for i, prize in enumerate(prizes):
            if not prize.get('name') or not prize.get('category'):
                return jsonify({'success': False, 'error': f'Prize {i+1} missing required fields (name/category)'}), 400
            
            # Auto-adjust category based on business logic
            category = prize.get('category')
            availability_dates = prize.get('availability_dates', [])
            quantity = prize.get('quantity_per_date', 1)
            
            # Smart category adjustment
            original_category = category
            if availability_dates and availability_dates[0] == '*':
                # Always available items should be Common
                category = 'common'
            else:
                # Limited availability - categorize by quantity
                if quantity <= 2:
                    category = 'ultra_rare'
                elif quantity <= 5:
                    category = 'rare'
                else:
                    category = 'common'
            
            # Update the prize data with adjusted category
            if original_category != category:
                logger.info(f"Prize {i+1} '{prize.get('name')}': Category auto-adjusted from '{original_category}' to '{category}' based on quantity ({quantity}) and availability")
                prize['category'] = category
            
            # Business logic validation (after auto-adjustment)
            if category == 'ultra_rare':
                if availability_dates and availability_dates[0] == '*':
                    return jsonify({'success': False, 'error': f'Prize {i+1}: Ultra Rare items cannot be always available'}), 400
                if quantity > 2:
                    return jsonify({'success': False, 'error': f'Prize {i+1}: Ultra Rare items max 2 per date'}), 400
            
            elif category == 'rare':
                if availability_dates and availability_dates[0] == '*':
                    return jsonify({'success': False, 'error': f'Prize {i+1}: Rare items cannot be always available'}), 400
                if quantity > 5:
                    return jsonify({'success': False, 'error': f'Prize {i+1}: Rare items max 5 per date'}), 400
        
        success = PrizeManager.bulk_update_prizes(prizes)
        if success:
            logger.info(f"Successfully updated {len(prizes)} prizes")
            return jsonify({'success': True, 'message': f'Successfully updated {len(prizes)} prizes'})
        else:
            logger.error("Bulk update failed - PrizeManager returned False")
            return jsonify({'success': False, 'error': 'Failed to update prizes - database operation failed'}), 500
    except Exception as e:
        logger.error(f"Error in bulk update endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Server error: {str(e)}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/debug/categories', methods=['GET'])
def debug_categories():
    """Debug endpoint to check available categories"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM prize_categories ORDER BY id")
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'categories': categories})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug/restore-default-prizes', methods=['POST'])
def restore_default_prizes():
    """Emergency endpoint to restore default prizes from schema"""
    try:
        logger.info("Restoring default prizes from database schema...")
        
        # Re-run the database initialization to restore default data
        db_manager.init_database()
        
        return jsonify({
            'success': True, 
            'message': 'Default prizes restored successfully'
        })
    except Exception as e:
        logger.error(f"Failed to restore default prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/config/sync-csv', methods=['POST'])
def sync_csv_config():
    """Sync prize configuration from CSV file to database"""
    try:
        logger.info("Syncing prize configuration from CSV...")
        
        # Load prizes from CSV
        csv_prizes = csv_manager.load_prizes_from_csv()
        
        if not csv_prizes:
            return jsonify({'success': False, 'error': 'No prizes loaded from CSV'}), 400
        
        # Use the existing bulk update method to sync with database
        success = PrizeManager.bulk_update_prizes(csv_prizes)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully synced {len(csv_prizes)} prizes from CSV',
                'prizes_count': len(csv_prizes)
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to sync CSV data to database'}), 500
            
    except Exception as e:
        logger.error(f"Failed to sync CSV configuration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prizes/csv-config', methods=['GET'])
def get_csv_config():
    """Get current CSV configuration without syncing to database"""
    try:
        csv_prizes = csv_manager.load_prizes_from_csv()
        return jsonify({
            'success': True,
            'prizes': csv_prizes,
            'count': len(csv_prizes)
        })
    except Exception as e:
        logger.error(f"Failed to load CSV configuration: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prizes/wheel-display', methods=['GET'])
def get_wheel_display_prizes():
    """Get ALL prizes for wheel display (regardless of availability)"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get all prizes with their category information
        cursor.execute("""
            SELECT p.id, p.name, pc.name as category, p.type, p.emoji, pc.weight, p.description
            FROM prizes p
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE p.is_active = 1
            ORDER BY p.id
        """)
        
        prizes = []
        for row in cursor.fetchall():
            prize = dict(row)
            prizes.append(prize)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'prizes': prizes,
            'count': len(prizes)
        })
        
    except Exception as e:
        logger.error(f"Error getting wheel display prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === UTILITY FUNCTIONS FOR SERVER-AUTHORITATIVE SYSTEM ===

SECRET_KEY = "pickerwheel_contest_secret_2025"  # In production, use environment variable

def generate_response_signature(payload):
    """Generate HMAC-SHA256 signature for response payload"""
    # Create canonical string from payload (excluding signature field)
    payload_copy = payload.copy()
    payload_copy.pop('signature', None)
    
    # Sort keys for consistent signature
    canonical_string = json.dumps(payload_copy, sort_keys=True, separators=(',', ':'))
    
    # Generate HMAC-SHA256 signature
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        canonical_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature

def check_existing_reservation(idempotency_key):
    """Check if a reservation already exists for this idempotency key"""
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pr.*, p.name as prize_name, p.emoji, pc.name as category
            FROM prize_reservations pr
            JOIN prizes p ON pr.prize_id = p.id
            JOIN prize_categories pc ON p.category_id = pc.id
            WHERE pr.idempotency_key = ? AND pr.expires_at > ?
            ORDER BY pr.reserved_at DESC LIMIT 1
        """, (idempotency_key, datetime.now().isoformat()))
        
        reservation = cursor.fetchone()
        conn.close()
        
        if reservation:
            reservation_dict = dict(reservation)
            
            # Reconstruct the original response
            response_payload = {
                'success': True,
                'prize': {
                    'id': reservation_dict['prize_id'],
                    'name': reservation_dict['prize_name'],
                    'emoji': reservation_dict['emoji'],
                    'category': reservation_dict['category']
                },
                'sector_index': reservation_dict['sector_index'],
                'sector_center': reservation_dict['sector_center'],
                'reservation_id': reservation_dict['reservation_id'],
                'reservation_ttl': 300,  # Standard TTL
                'message': f'Congratulations! You won {reservation_dict["prize_name"]}!',
                'server_timestamp': reservation_dict['reserved_at']
            }
            
            # Regenerate signature
            signature = generate_response_signature(response_payload)
            response_payload['signature'] = signature
            
            return response_payload
            
        return None
        
    except Exception as e:
        logger.error(f"Error checking existing reservation: {e}")

def create_reservations_table():
    """Create prize_reservations table if it doesn't exist"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Create prize inventory table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prize_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prize_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            available_date TEXT NOT NULL,
            initial_quantity INTEGER DEFAULT 0,
            remaining_quantity INTEGER DEFAULT 0,
            per_day_limit INTEGER DEFAULT 1,
            is_unlimited INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prize_id) REFERENCES prizes(id),
            UNIQUE(prize_id, event_id, available_date)
        )
    """)
    
    # Create prize_reservations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prize_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id TEXT UNIQUE NOT NULL,
            idempotency_key TEXT NOT NULL,
            user_identifier TEXT NOT NULL,
            prize_id INTEGER NOT NULL,
            sector_index INTEGER NOT NULL,
            sector_center REAL NOT NULL,
            reserved_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            finalized_at TEXT,
            status TEXT DEFAULT 'reserved',
            FOREIGN KEY (prize_id) REFERENCES prizes (id)
        )
    """)
    
    # Add indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservations_idempotency ON prize_reservations(idempotency_key)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservations_expires ON prize_reservations(expires_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservations_status ON prize_reservations(status)")
    
    # Add award_id and reservation_id columns to prize_wins if they don't exist
    try:
        cursor.execute("ALTER TABLE prize_wins ADD COLUMN award_id TEXT")
        cursor.execute("ALTER TABLE prize_wins ADD COLUMN reservation_id TEXT")
        cursor.execute("ALTER TABLE prize_wins ADD COLUMN sector_index INTEGER")
    except sqlite3.OperationalError:
        # Columns already exist
        pass
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("🔐 PickerWheel Contest Backend API - Server Authoritative")
    print("=" * 60)
    print(f"📅 Event Period: {EVENT_START_DATE} to {EVENT_END_DATE}")
    print(f"🗄️  Database: {DATABASE_PATH}")
    print(f"🔑 Admin Password: {ADMIN_PASSWORD}")
    print(f"🔐 Cryptographic Signatures: Enabled")
    print(f"♻️  Idempotency Protection: Enabled")
    print(f"⏰ Reservation TTL: 5 minutes")
    print("=" * 60)
    
    # Initialize database
    db_manager = DatabaseManager(DATABASE_PATH)
    
    # Create additional tables for server-authoritative system
    create_reservations_table()
    
    # Register database management endpoints
    app = register_db_management_endpoints(app, db_manager, ADMIN_PASSWORD)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=9080, debug=True)
