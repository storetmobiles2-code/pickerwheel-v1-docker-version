#!/usr/bin/env python3
"""
Daily PickerWheel Contest Backend API with Database
Hybrid approach: Uses database for transactions/inventory but loads daily CSV data
Created: September 23, 2025
"""

import sqlite3
import csv
import json
import logging
import os
import random
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_PATH = 'pickerwheel_contest.db'
DAILY_CSV_DIR = '/app/daily_csvs' if os.path.exists('/app') else 'daily_csvs'
PORT = 9082  # Different port for testing
ADMIN_PASSWORD = 'myTAdmin2025'
EVENT_ID = 1

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create tables if they don't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_prizes (
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_inventory (
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_transactions (
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_prizes_date ON daily_prizes(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_inventory_date ON daily_inventory(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_transactions_date ON daily_transactions(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date)')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            conn.rollback()
        finally:
            conn.close()

class DailyPrizeManager:
    """Manages daily prizes with database persistence"""
    
    def __init__(self, csv_dir: str, db_manager: DatabaseManager):
        self.csv_dir = csv_dir
        self.db_manager = db_manager
        self.current_date = None
        self.current_prizes = []
        
    def load_all_prizes_from_itemlist(self) -> List[Dict]:
        """Load ALL prizes from itemlist_dates.txt (for wheel display)"""
        # Try multiple possible paths
        possible_paths = [
            '/app/itemlist_dates.txt',  # Docker path
            'itemlist_dates.txt',       # Current directory
            '../itemlist_dates.txt',    # Parent directory
            os.path.join(os.path.dirname(__file__), '..', 'itemlist_dates.txt')  # Relative to backend
        ]
        
        itemlist_path = None
        for path in possible_paths:
            if os.path.exists(path):
                itemlist_path = path
                break
        
        if not itemlist_path:
            logger.error(f"Itemlist file not found. Tried paths: {possible_paths}")
            return []
            
        prizes = []
        try:
            with open(itemlist_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
                
                # Skip header line
                if lines and lines[0].startswith('Item,'):
                    lines = lines[1:]
                
                for i, line in enumerate(lines):
                    if not line:
                        continue
                        
                    parts = line.split(',')
                    if len(parts) >= 5:
                        item_name = parts[0].strip()
                        category = parts[1].strip()
                        quantity = parts[2].strip()
                        daily_limit = parts[3].strip()
                        available_dates = parts[4].strip()
                        
                        prize = {
                            'id': i + 1,
                            'name': item_name,
                            'category': category.lower().replace(' ', '_'),
                            'quantity': int(quantity) if quantity.isdigit() else 0,
                            'daily_limit': int(daily_limit) if daily_limit.isdigit() else 1,
                            'available_dates': available_dates,
                            'emoji': self._get_emoji_for_prize(item_name)
                        }
                        prizes.append(prize)
                        
            logger.info(f"Loaded {len(prizes)} total prizes from itemlist_dates.txt")
            return prizes
            
        except Exception as e:
            logger.error(f"Error loading itemlist: {e}")
            return []
    
    def load_daily_prizes_from_csv(self, target_date: date) -> List[Dict]:
        """Load prizes for a specific date from CSV file (DEPRECATED - use load_all_prizes_from_itemlist)"""
        # This method is kept for backward compatibility but should not be used
        # The wheel should always show ALL items from itemlist_dates.txt
        return self.load_all_prizes_from_itemlist()
    
    def sync_daily_prizes_to_database(self, target_date: date) -> bool:
        """Sync daily prizes from CSV to database"""
        date_str = target_date.isoformat()
        csv_prizes = self.load_daily_prizes_from_csv(target_date)
        
        if not csv_prizes:
            return False
            
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing prizes for this date
            cursor.execute('DELETE FROM daily_prizes WHERE date = ?', (date_str,))
            cursor.execute('DELETE FROM daily_inventory WHERE date = ?', (date_str,))
            
            # Insert new prizes
            for prize in csv_prizes:
                cursor.execute('''
                    INSERT INTO daily_prizes (date, prize_name, category, quantity, daily_limit, emoji)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date_str, prize['name'], prize['category'], prize['quantity'], 
                      prize['daily_limit'], prize['emoji']))
                
                # Initialize inventory
                cursor.execute('''
                    INSERT INTO daily_inventory (date, prize_name, initial_quantity, remaining_quantity, daily_limit)
                    VALUES (?, ?, ?, ?, ?)
                ''', (date_str, prize['name'], prize['quantity'], prize['quantity'], prize['daily_limit']))
            
            # Initialize daily stats
            cursor.execute('''
                INSERT OR REPLACE INTO daily_stats (date, total_prizes, total_wins, unique_users)
                VALUES (?, ?, 0, 0)
            ''', (date_str, len(csv_prizes)))
            
            conn.commit()
            logger.info(f"Synced {len(csv_prizes)} prizes to database for {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing daily prizes to database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_all_prizes_for_wheel(self, target_date: date = None) -> List[Dict]:
        """Get ALL prizes for wheel display (from database)"""
        if target_date is None:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # First, sync all items to database
            self.sync_all_items_to_database(target_date)
            
            # Get all prizes from database (including those with 0 quantity)
            cursor.execute('''
                SELECT dp.prize_id as id, dp.name, dp.category, dp.quantity, dp.daily_limit, 
                       dp.available_dates, dp.emoji, di.remaining_quantity
                FROM daily_prizes dp
                JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
                WHERE dp.date = ?
                ORDER BY dp.prize_id
            ''', (date_str,))
            
            all_prizes = []
            for row in cursor.fetchall():
                prize = dict(row)
                all_prizes.append(prize)
            
            logger.info(f"Retrieved {len(all_prizes)} prizes for wheel display from database")
            return all_prizes
            
        except Exception as e:
            logger.error(f"Error getting wheel display prizes: {e}")
            # Fallback to itemlist if database fails
            return self.load_all_prizes_from_itemlist()
        finally:
            conn.close()
    
    def get_daily_prizes_from_database(self, target_date: date) -> List[Dict]:
        """Get daily prizes from database (DEPRECATED - use get_all_prizes_for_wheel)"""
        # This method is kept for backward compatibility
        # The wheel should always show ALL items from itemlist_dates.txt
        return self.get_all_prizes_for_wheel()
    
    def is_item_available_on_date(self, item: Dict, target_date: date) -> bool:
        """Check if an item is available on a specific date"""
        available_dates = item['available_dates']
        
        # If "*", item is available on all days
        if available_dates == '*':
            return True
        
        # Check if target date is in the available dates list
        date_str = target_date.isoformat()
        available_date_list = [d.strip() for d in available_dates.split('|')]
        
        return date_str in available_date_list
    
    def sync_all_items_to_database(self, target_date: date) -> bool:
        """Sync all items from itemlist_dates.txt to database with proper quantities"""
        all_prizes = self.load_all_prizes_from_itemlist()
        date_str = target_date.isoformat()
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing data for this date
            cursor.execute('DELETE FROM daily_prizes WHERE date = ?', (date_str,))
            cursor.execute('DELETE FROM daily_inventory WHERE date = ?', (date_str,))
            
            for prize in all_prizes:
                # Determine if item is available on this date
                is_available = self.is_item_available_on_date(prize, target_date)
                
                # Set quantity based on availability
                if is_available:
                    quantity = prize['quantity']
                else:
                    quantity = 0  # Not available today
                
                # Insert into daily_prizes table
                cursor.execute('''
                    INSERT INTO daily_prizes (date, prize_id, name, category, quantity, daily_limit, available_dates, emoji)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    prize['id'],
                    prize['name'],
                    prize['category'],
                    quantity,
                    prize['daily_limit'],
                    prize['available_dates'],
                    prize.get('emoji', '🎁')
                ))
                
                # Insert into daily_inventory table
                cursor.execute('''
                    INSERT INTO daily_inventory (date, prize_id, name, initial_quantity, remaining_quantity, daily_limit)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    date_str,
                    prize['id'],
                    prize['name'],
                    quantity,
                    quantity,
                    prize['daily_limit']
                ))
            
            conn.commit()
            logger.info(f"Synced {len(all_prizes)} items to database for {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing items to database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_available_prizes(self, target_date: date) -> List[Dict]:
        """Get available prizes for a specific date with daily limit enforcement"""
        date_str = target_date.isoformat()
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # First, sync all items to database
            self.sync_all_items_to_database(target_date)
            
            # Get available prizes with daily limit checking
            cursor.execute('''
                SELECT dp.prize_id as id, dp.name, dp.category, dp.quantity, dp.daily_limit, 
                       dp.available_dates, dp.emoji, di.remaining_quantity,
                       COALESCE(today_wins.wins_today, 0) as wins_today
                FROM daily_prizes dp
                JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
                LEFT JOIN (
                    SELECT prize_id, COUNT(*) as wins_today
                    FROM daily_transactions 
                    WHERE date = ? AND transaction_type = 'win'
                    GROUP BY prize_id
                ) today_wins ON dp.prize_id = today_wins.prize_id
                WHERE dp.date = ? 
                  AND di.remaining_quantity > 0
                  AND COALESCE(today_wins.wins_today, 0) < dp.daily_limit
                ORDER BY dp.prize_id
            ''', (date_str, date_str))
            
            available_prizes = []
            for row in cursor.fetchall():
                prize = dict(row)
                available_prizes.append(prize)
            
            logger.info(f"Found {len(available_prizes)} available prizes for {date_str} (after daily limit filtering)")
            
            # Debug logging for daily limits
            if logger.isEnabledFor(logging.DEBUG):
                cursor.execute('''
                    SELECT dp.name, dp.daily_limit, COALESCE(today_wins.wins_today, 0) as wins_today,
                           di.remaining_quantity
                    FROM daily_prizes dp
                    JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
                    LEFT JOIN (
                        SELECT prize_id, COUNT(*) as wins_today
                        FROM daily_transactions 
                        WHERE date = ? AND transaction_type = 'win'
                        GROUP BY prize_id
                    ) today_wins ON dp.prize_id = today_wins.prize_id
                    WHERE dp.date = ?
                    ORDER BY dp.name
                ''', (date_str, date_str))
                
                logger.debug(f"Daily limit status for {date_str}:")
                for row in cursor.fetchall():
                    status = "AVAILABLE" if row['wins_today'] < row['daily_limit'] and row['remaining_quantity'] > 0 else "EXHAUSTED"
                    logger.debug(f"  {row['name']}: {row['wins_today']}/{row['daily_limit']} daily, {row['remaining_quantity']} remaining - {status}")
            
            return available_prizes
            
        except Exception as e:
            logger.error(f"Error getting available prizes: {e}")
            return []
        finally:
            conn.close()
    
    def select_prize_with_priority(self, target_date: date, user_identifier: str) -> Optional[Dict]:
        """Select a prize with priority for rare/ultra rare items and daily limit enforcement"""
        available_prizes = self.get_available_prizes(target_date)
        
        if not available_prizes:
            logger.warning(f"No available prizes for {target_date}")
            return None
        
        # Separate prizes by category
        ultra_rare = [p for p in available_prizes if p['category'].lower() == 'ultra_rare']
        rare = [p for p in available_prizes if p['category'].lower() == 'rare']
        common = [p for p in available_prizes if p['category'].lower() == 'common']
        
        logger.info(f"Prize availability: {len(ultra_rare)} ultra-rare, {len(rare)} rare, {len(common)} common")
        
        # Get today's win statistics for better distribution
        date_str = target_date.isoformat()
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get today's win statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_wins,
                    SUM(CASE WHEN dp.category IN ('rare', 'ultra_rare') THEN 1 ELSE 0 END) as rare_wins
                FROM daily_transactions dt
                JOIN daily_prizes dp ON dt.prize_id = dp.prize_id AND dt.date = dp.date
                WHERE dt.date = ? AND dt.transaction_type = 'win'
            ''', (date_str,))
            
            stats = cursor.fetchone()
            total_wins = stats['total_wins'] if stats and stats['total_wins'] else 0
            rare_wins = stats['rare_wins'] if stats and stats['rare_wins'] else 0
            
            # Calculate rare item percentage
            rare_percentage = rare_wins / total_wins if total_wins > 0 else 0
            target_rare_percentage = 0.30  # Target 30% rare items
            
            logger.info(f"Today's stats: {total_wins} total wins, {rare_wins} rare wins ({rare_percentage:.1%})")
            
            # Force rare item selection if we're below target and rare items are available
            force_rare = (rare_percentage < target_rare_percentage) and (ultra_rare or rare)
            
            # Selection logic with enhanced rare item priority
            selected_prize = None
            
            if force_rare or ((ultra_rare or rare) and random.random() < 0.5):
                # 50% chance for rare items, or forced if below target
                logger.info("🎯 Selecting from rare/ultra-rare items")
                if ultra_rare and random.random() < 0.3:  # 30% chance for ultra-rare if available
                    selected_prize = random.choice(ultra_rare)
                    logger.info(f"Selected ultra-rare: {selected_prize['name']}")
                elif rare:
                    selected_prize = random.choice(rare)
                    logger.info(f"Selected rare: {selected_prize['name']}")
            
            # If no rare item selected, pick from common
            if not selected_prize and common:
                selected_prize = random.choice(common)
                logger.info(f"Selected common: {selected_prize['name']}")
            
            # Final fallback to any available prize
            if not selected_prize:
                selected_prize = random.choice(available_prizes)
                logger.info(f"Fallback selection: {selected_prize['name']}")
            
            # Log selection details
            if selected_prize:
                logger.info(f"🎲 Prize selected: {selected_prize['name']} ({selected_prize['category']}) - "
                           f"Wins today: {selected_prize.get('wins_today', 0)}/{selected_prize['daily_limit']}, "
                           f"Remaining: {selected_prize['remaining_quantity']}")
            
            return selected_prize
            
        except Exception as e:
            logger.error(f"Error in prize selection: {e}")
            # Fallback to simple random selection
            return random.choice(available_prizes) if available_prizes else None
        finally:
            conn.close()
    
    def consume_prize(self, prize_id: int, prize_name: str, target_date: date, user_identifier: str) -> bool:
        """Consume a prize and record transaction"""
        date_str = target_date.isoformat()
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Record transaction
            cursor.execute('''
                INSERT INTO daily_transactions (date, prize_id, name, user_identifier, transaction_type, quantity)
                VALUES (?, ?, ?, ?, 'win', 1)
            ''', (date_str, prize_id, prize_name, user_identifier))
            
            # Update inventory
            cursor.execute('''
                UPDATE daily_inventory
                SET remaining_quantity = remaining_quantity - 1
                WHERE date = ? AND prize_id = ?
            ''', (date_str, prize_id))
            
            # Update daily stats
            cursor.execute('''
                UPDATE daily_stats
                SET total_wins = total_wins + 1
                WHERE date = ?
            ''', (date_str,))
            
            # Update unique users count
            cursor.execute('''
                SELECT COUNT(DISTINCT user_identifier) as unique_count
                FROM daily_transactions
                WHERE date = ? AND transaction_type = 'win'
            ''', (date_str,))
            
            unique_count = cursor.fetchone()['unique_count']
            cursor.execute('''
                UPDATE daily_stats
                SET unique_users = ?
                WHERE date = ?
            ''', (unique_count, date_str))
            
            conn.commit()
            logger.info(f"Prize consumed: {prize_name} by {user_identifier} on {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error consuming prize: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_daily_stats(self, target_date: date) -> Dict:
        """Get daily statistics"""
        date_str = target_date.isoformat()
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get total prizes from itemlist
            all_prizes = self.get_all_prizes_for_wheel()
            total_prizes = len(all_prizes)
            
            # Get available prizes count
            available_prizes = self.get_available_prizes(target_date)
            
            # Get wins and unique users from database
            cursor.execute('''
                SELECT COUNT(*) as total_wins
                FROM daily_transactions
                WHERE date = ? AND transaction_type = 'win'
            ''', (date_str,))
            total_wins = cursor.fetchone()['total_wins']
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_identifier) as unique_users
                FROM daily_transactions
                WHERE date = ? AND transaction_type = 'win'
            ''', (date_str,))
            unique_users = cursor.fetchone()['unique_users']
            
            # Get category breakdown for available prizes
            category_breakdown = {}
            for prize in available_prizes:
                cat = prize['category']
                category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
            
            return {
                'date': date_str,
                'total_prizes': total_prizes,
                'available_prizes': len(available_prizes),
                'total_wins_today': total_wins,
                'unique_users': unique_users,
                'category_breakdown': category_breakdown
            }
            
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {
                'date': date_str,
                'total_prizes': 0,
                'available_prizes': 0,
                'total_wins_today': 0,
                'unique_users': 0,
                'category_breakdown': {}
            }
        finally:
            conn.close()
    
    def _get_emoji_for_prize(self, name: str) -> str:
        """Get appropriate emoji for prize based on name"""
        name_lower = name.lower()
        
        if 'tv' in name_lower or 'television' in name_lower:
            return '📺'
        elif 'phone' in name_lower or 'mobile' in name_lower or 'smartphone' in name_lower:
            return '📱'
        elif 'tab' in name_lower or 'tablet' in name_lower:
            return '📱'
        elif 'watch' in name_lower or 'smartwatch' in name_lower:
            return '⌚'
        elif 'speaker' in name_lower or 'soundbar' in name_lower:
            return '🔊'
        elif 'theatre' in name_lower or 'theater' in name_lower:
            return '🎭'
        elif 'refrigerator' in name_lower or 'fridge' in name_lower:
            return '🧊'
        elif 'washing' in name_lower or 'machine' in name_lower:
            return '🧺'
        elif 'cooler' in name_lower or 'air' in name_lower:
            return '❄️'
        elif 'coin' in name_lower or 'silver' in name_lower:
            return '🪙'
        elif 'stove' in name_lower or 'gas' in name_lower:
            return '🔥'
        elif 'grinder' in name_lower or 'mixer' in name_lower:
            return '🥤'
        elif 'luggage' in name_lower or 'bag' in name_lower:
            return '🧳'
        elif 'cooker' in name_lower or 'pressure' in name_lower:
            return '🍲'
        elif 'pouch' in name_lower or 'screen' in name_lower:
            return '📱'
        elif 'dinner' in name_lower or 'set' in name_lower:
            return '🍽️'
        elif 'earbud' in name_lower or 'buds' in name_lower:
            return '🎧'
        elif 'power' in name_lower or 'bank' in name_lower:
            return '🔋'
        elif 'neckband' in name_lower:
            return '🎵'
        elif 'trimmer' in name_lower:
            return '✂️'
        else:
            return '🎁'

# Initialize managers
db_manager = DatabaseManager(DATABASE_PATH)
prize_manager = DailyPrizeManager(DAILY_CSV_DIR, db_manager)

# API Routes

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('../frontend', filename)

@app.route('/api/prizes/wheel-display')
def get_wheel_display_prizes():
    """Get ALL prizes for wheel display (from database)"""
    try:
        # Get target date from query parameter or use today
        target_date_str = request.args.get('date')
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Get all prizes from database (including those with 0 quantity)
        prizes = prize_manager.get_all_prizes_for_wheel(target_date)
        
        return jsonify({
            'success': True,
            'prizes': prizes,
            'total_items': len(prizes),
            'date': target_date.isoformat(),
            'source': 'database'
        })
        
    except Exception as e:
        logger.error(f"Error getting wheel display prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/prizes/available')
def get_available_prizes():
    """Get available prizes for today or specified date"""
    try:
        target_date = request.args.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
            
        prizes = prize_manager.get_available_prizes(target_date)
        
        return jsonify({
            'success': True,
            'prizes': prizes,
            'date': target_date.isoformat()
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
        
        # Get target date
        target_date = data.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        logger.info(f"Pre-spin request - User: {user_identifier}, Date: {target_date}")
        
        # Get available prizes for the date
        available_prizes = prize_manager.get_available_prizes(target_date)
        
        if not available_prizes:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
        
        # Select prize with priority logic
        selected_prize = prize_manager.select_prize_with_priority(target_date, user_identifier)
        
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
        
        # Get ALL wheel display prizes to calculate target segment
        all_wheel_prizes = prize_manager.get_all_prizes_for_wheel()
        
        # Find target segment index for this prize in the full wheel using ID mapping
        target_segment_index = next(
            (i for i, prize in enumerate(all_wheel_prizes) if prize['id'] == selected_prize['id']), 
            0
        )
        
        logger.info(f"🎯 MAPPING DEBUG:")
        logger.info(f"   Selected available prize: {selected_prize['name']} ({selected_prize['category']})")
        logger.info(f"   Maps to wheel segment: {target_segment_index}")
        logger.info(f"   Wheel prize at segment {target_segment_index}: {all_wheel_prizes[target_segment_index]['name']}")
        
        # Verify the mapping is correct using ID
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
                'selected_prize_name': selected_prize['name'],
                'all_prize_ids': [p['id'] for p in all_wheel_prizes],
                'all_prize_names': [p['name'] for p in all_wheel_prizes],
                'mapping': [(i, p['id'], p['name']) for i, p in enumerate(all_wheel_prizes)]
            }
        })
        
    except Exception as e:
        logger.error(f"Error in pre-spin selection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/spin', methods=['POST'])
def spin_wheel():
    """Handle wheel spin with pre-selected prize"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        selected_prize_id = data.get('selected_prize_id')
        target_segment_index = data.get('target_segment_index', 0)
        final_rotation = data.get('final_rotation', 0)
        
        # Get target date
        target_date = data.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        logger.info(f"Spin confirmation - User: {user_identifier}, Prize ID: {selected_prize_id}, Segment: {target_segment_index}")
        
        if not selected_prize_id:
            return jsonify({
                'success': False,
                'error': 'No prize ID provided'
            }), 400
        
        # Get available prizes to verify the pre-selected prize is still available
        available_prizes = prize_manager.get_available_prizes(target_date)
        
        # Find the selected prize in available prizes
        selected_prize = None
        for prize in available_prizes:
            if prize['id'] == selected_prize_id:
                selected_prize = prize
                break
        
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'Selected prize is no longer available'
            }), 400
        
        # Consume the prize and record transaction
        success = prize_manager.consume_prize(selected_prize['id'], selected_prize['name'], target_date, user_identifier)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Failed to process prize'
            }), 500
        
        # Calculate sector center
        all_wheel_prizes = prize_manager.get_all_prizes_for_wheel()
        sector_angle = 360 / len(all_wheel_prizes) if all_wheel_prizes else 360
        sector_center = target_segment_index * sector_angle + (sector_angle / 2)
        
        logger.info(f"User {user_identifier} won {selected_prize['name']} on {target_date}")
        
        return jsonify({
            'success': True,
            'prize': selected_prize,
            'sector_index': target_segment_index,
            'sector_center': sector_center,
            'total_segments': len(all_wheel_prizes),
            'user_id': user_identifier,
            'date': target_date.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in spin wheel: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get daily statistics"""
    try:
        target_date = request.args.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
            
        stats = prize_manager.get_daily_stats(target_date)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/load-date', methods=['POST'])
def admin_load_date():
    """Admin endpoint to load prizes for a specific date"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
        target_date_str = data.get('date')
        if not target_date_str:
            return jsonify({'success': False, 'error': 'Date required'}), 400
            
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        success = prize_manager.sync_daily_prizes_to_database(target_date)
        
        if success:
            prizes = prize_manager.get_daily_prizes_from_database(target_date)
            return jsonify({
                'success': True,
                'prizes': prizes,
                'date': target_date.isoformat(),
                'count': len(prizes)
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to load date'}), 500
        
    except Exception as e:
        logger.error(f"Error in admin load date: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/transactions', methods=['GET'])
def admin_get_transactions():
    """Admin endpoint to get transaction history"""
    try:
        data = request.get_json() or {}
        admin_password = request.args.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
        target_date = request.args.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT prize_id, name, user_identifier, transaction_type, quantity, timestamp
                FROM daily_transactions
                WHERE date = ?
                ORDER BY timestamp DESC
            ''', (date_str,))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'prize_id': row['prize_id'],
                    'name': row['name'],
                    'user_identifier': row['user_identifier'],
                    'transaction_type': row['transaction_type'],
                    'quantity': row['quantity'],
                    'timestamp': row['timestamp']
                })
            
            return jsonify({
                'success': True,
                'transactions': transactions,
                'date': date_str
            })
            
        finally:
            conn.close()
        
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Daily PickerWheel Backend with Database on port {PORT}")
    logger.info(f"Daily CSV directory: {DAILY_CSV_DIR}")
    logger.info(f"Database path: {DATABASE_PATH}")
    
    # Test loading today's prizes
    try:
        today_prizes = prize_manager.sync_daily_prizes_to_database(date.today())
        logger.info(f"Synced daily prizes for today: {today_prizes}")
    except Exception as e:
        logger.error(f"Failed to sync today's prizes: {e}")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
