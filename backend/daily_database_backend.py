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
            # ✅ FIX: Preserve existing inventory and transaction history
            cursor.execute('SELECT COUNT(*) FROM daily_prizes WHERE date = ?', (date_str,))
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                logger.info(f"📊 Data already exists for {date_str} ({existing_count} prizes), preserving transaction history and inventory")
                return True
            
            logger.info(f"📊 First sync for {date_str}, initializing fresh database...")
            
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
            
            # ✅ FIX: Add database integrity check after sync
            self._validate_database_integrity(target_date)
            return True
            
        except Exception as e:
            logger.error(f"Error syncing items to database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def sync_all_dates_to_database(self) -> bool:
        """🗓️ Sync ALL dates from itemlist_dates_v2.txt to database (Multi-date support)"""
        all_prizes = self.load_all_prizes_from_itemlist()
        
        # Extract all unique dates from the prizes
        all_dates = set()
        for prize in all_prizes:
            if prize['available_dates'] == '*':
                # For '*', add a range of dates (current date to Oct 30, 2025)
                start_date = date.today()
                end_date = date(2025, 10, 30)
                current = start_date
                while current <= end_date:
                    all_dates.add(current.isoformat())
                    current += timedelta(days=1)
            else:
                # Add specific dates
                date_list = [d.strip() for d in prize['available_dates'].split('|')]
                all_dates.update(date_list)
        
        logger.info(f"🗓️ Syncing {len(all_dates)} dates to database...")
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            synced_dates = 0
            for date_str in sorted(all_dates):
                try:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # Check if data already exists for this date
                    cursor.execute('SELECT COUNT(*) FROM daily_prizes WHERE date = ?', (date_str,))
                    existing_count = cursor.fetchone()[0]
                    
                    if existing_count > 0:
                        logger.debug(f"📊 Data already exists for {date_str} ({existing_count} prizes), skipping")
                        continue
                    
                    # Sync this specific date
                    for prize in all_prizes:
                        # Determine if item is available on this date
                        is_available = self.is_item_available_on_date(prize, target_date)
                        
                        # Set quantity based on availability
                        if is_available:
                            quantity = prize['quantity']
                        else:
                            quantity = 0  # Not available on this date
                        
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
                    
                    synced_dates += 1
                    if synced_dates % 10 == 0:  # Log progress every 10 dates
                        logger.info(f"📊 Synced {synced_dates} dates so far...")
                        
                except ValueError as e:
                    logger.warning(f"Invalid date format: {date_str}, skipping")
                    continue
            
            conn.commit()
            logger.info(f"✅ Successfully synced {synced_dates} new dates to database")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing all dates to database: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def _validate_database_integrity(self, target_date: date):
        """✅ FIX: Validate database integrity and consistency"""
        date_str = target_date.isoformat()
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check 1: Verify no negative quantities
            cursor.execute('''
                SELECT COUNT(*) FROM daily_inventory 
                WHERE date = ? AND remaining_quantity < 0
            ''', (date_str,))
            
            negative_count = cursor.fetchone()[0]
            if negative_count > 0:
                logger.warning(f"⚠️ Found {negative_count} items with negative quantities for {date_str}")
            
            # Check 2: Verify daily limits aren't exceeded
            cursor.execute('''
                SELECT dp.name, dp.daily_limit, COUNT(dt.prize_id) as actual_wins
                FROM daily_prizes dp
                LEFT JOIN daily_transactions dt ON dp.prize_id = dt.prize_id AND dp.date = dt.date
                WHERE dp.date = ? AND dt.transaction_type = 'win'
                GROUP BY dp.prize_id, dp.name, dp.daily_limit
                HAVING COUNT(dt.prize_id) > dp.daily_limit
            ''', (date_str,))
            
            violations = cursor.fetchall()
            if violations:
                for violation in violations:
                    logger.warning(f"⚠️ Daily limit exceeded: {violation['name']} - {violation['actual_wins']}/{violation['daily_limit']}")
            
            logger.debug(f"✅ Database integrity check completed for {date_str}")
            
        except Exception as e:
            logger.error(f"Error during integrity check: {e}")
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
        """Select a prize with AGGRESSIVE priority for rare/ultra rare items (3-5 spin guarantee)"""
        available_prizes = self.get_available_prizes(target_date)
        
        if not available_prizes:
            logger.warning(f"No available prizes for {target_date}")
            return None
        
        # Separate prizes by category
        ultra_rare = [p for p in available_prizes if p['category'].lower() == 'ultra_rare']
        rare = [p for p in available_prizes if p['category'].lower() == 'rare']
        common = [p for p in available_prizes if p['category'].lower() == 'common']
        
        logger.info(f"Prize availability: {len(ultra_rare)} ultra-rare, {len(rare)} rare, {len(common)} common")
        
        # Get today's win statistics for aggressive selection
        date_str = target_date.isoformat()
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get today's win statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_wins,
                    SUM(CASE WHEN dp.category = 'ultra_rare' THEN 1 ELSE 0 END) as ultra_rare_wins,
                    SUM(CASE WHEN dp.category = 'rare' THEN 1 ELSE 0 END) as rare_wins,
                    SUM(CASE WHEN dp.category IN ('rare', 'ultra_rare') THEN 1 ELSE 0 END) as total_rare_wins
                FROM daily_transactions dt
                JOIN daily_prizes dp ON dt.prize_id = dp.prize_id AND dt.date = dp.date
                WHERE dt.date = ? AND dt.transaction_type = 'win'
            ''', (date_str,))
            
            stats = cursor.fetchone()
            total_wins = stats['total_wins'] if stats and stats['total_wins'] else 0
            ultra_rare_wins = stats['ultra_rare_wins'] if stats and stats['ultra_rare_wins'] else 0
            rare_wins = stats['rare_wins'] if stats and stats['rare_wins'] else 0
            total_rare_wins = stats['total_rare_wins'] if stats and stats['total_rare_wins'] else 0
            
            logger.info(f"🎯 AGGRESSIVE SELECTION - Today's stats: {total_wins} total, {ultra_rare_wins} ultra-rare, {rare_wins} rare")
            
            # SUPER AGGRESSIVE SELECTION LOGIC FOR GUARANTEED 3-5 SPIN WINS
            selected_prize = None
            selection_reason = ""
            
            # PRIORITY 1: FORCE ultra-rare items in first 2 spins (95% chance)
            if ultra_rare and total_wins < 2:
                # 95% chance for ultra-rare in first 2 spins
                if random.random() < 0.95:
                    selected_prize = self._weighted_selection(ultra_rare, "ultra_rare")
                    selection_reason = f"🚀 ULTRA-RARE FORCE (spin #{total_wins + 1}/2) - 95% chance"
            
            # PRIORITY 2: FORCE rare items in spin 1-3 if no ultra-rare (90% chance)
            if not selected_prize and rare and total_wins < 3 and ultra_rare_wins == 0:
                # 90% chance for rare in first 3 spins if no ultra-rare won
                if random.random() < 0.90:
                    selected_prize = self._weighted_selection(rare, "rare")
                    selection_reason = f"🎯 RARE FORCE (spin #{total_wins + 1}/3) - 90% chance"
            
            # PRIORITY 3: ABSOLUTE GUARANTEE by spin 3-5 if no rare/ultra-rare won
            if not selected_prize and (rare or ultra_rare) and total_wins >= 2 and total_rare_wins == 0:
                # 100% guarantee rare/ultra-rare by spin 3-5
                if ultra_rare:
                    selected_prize = self._weighted_selection(ultra_rare, "ultra_rare")
                    selection_reason = f"⚡ ULTRA-RARE GUARANTEE (spin #{total_wins + 1}) - 100% FORCE"
                elif rare:
                    selected_prize = self._weighted_selection(rare, "rare")
                    selection_reason = f"⚡ RARE GUARANTEE (spin #{total_wins + 1}) - 100% FORCE"
            
            # PRIORITY 4: High chance for rare items even after one rare won (to respect daily limits)
            if not selected_prize and (rare or ultra_rare) and total_wins < 5:
                if ultra_rare and random.random() < 0.7:  # 70% ultra-rare
                    selected_prize = self._weighted_selection(ultra_rare, "ultra_rare")
                    selection_reason = f"🎯 ULTRA-RARE HIGH PRIORITY (spin #{total_wins + 1})"
                elif rare and random.random() < 0.8:  # 80% rare
                    selected_prize = self._weighted_selection(rare, "rare")
                    selection_reason = f"🎯 RARE HIGH PRIORITY (spin #{total_wins + 1})"
            
            # PRIORITY 5: Normal weighted selection for remaining spins
            if not selected_prize:
                if ultra_rare and random.random() < 0.5:  # 50% ultra-rare
                    selected_prize = self._weighted_selection(ultra_rare, "ultra_rare")
                    selection_reason = "🎲 Normal ultra-rare selection"
                elif rare and random.random() < 0.6:  # 60% rare
                    selected_prize = self._weighted_selection(rare, "rare")
                    selection_reason = "🎲 Normal rare selection"
                elif common:
                    selected_prize = self._weighted_selection(common, "common")
                    selection_reason = "🎲 Common selection"
            
            # Final fallback
            if not selected_prize:
                selected_prize = random.choice(available_prizes)
                selection_reason = "🔄 Fallback selection"
            
            # Log selection details
            if selected_prize:
                logger.info(f"🎲 {selection_reason}: {selected_prize['name']} ({selected_prize['category']}) - "
                           f"Wins today: {selected_prize.get('wins_today', 0)}/{selected_prize['daily_limit']}, "
                           f"Remaining: {selected_prize['remaining_quantity']}")
                
                # 🔧 FIX: Convert SQLite Row to dict for JSON serialization
                if hasattr(selected_prize, 'keys'):
                    selected_prize = dict(selected_prize)
            
            return selected_prize
            
        except Exception as e:
            logger.error(f"Error in aggressive prize selection: {e}")
            # Fallback to simple random selection
            if available_prizes:
                fallback_prize = random.choice(available_prizes)
                # 🔧 FIX: Convert SQLite Row to dict for JSON serialization
                if hasattr(fallback_prize, 'keys'):
                    fallback_prize = dict(fallback_prize)
                return fallback_prize
            return None
        finally:
            conn.close()
    
    def _weighted_selection(self, prizes: List[Dict], category: str) -> Dict:
        """Weighted selection within a category based on remaining quantity and daily limits"""
        if not prizes:
            return None
        
        # Calculate weights based on scarcity (lower remaining = higher weight)
        weighted_prizes = []
        for prize in prizes:
            # Base weight inversely proportional to remaining quantity
            base_weight = max(1, 10 - prize['remaining_quantity'])
            
            # Boost weight for items with fewer wins today
            wins_today = prize.get('wins_today', 0)
            daily_limit = prize['daily_limit']
            availability_boost = max(1, daily_limit - wins_today)
            
            # Category-specific multipliers (SUPER BOOSTED)
            if category == "ultra_rare":
                category_multiplier = 50  # 50x boost for ultra-rare (was 10x)
            elif category == "rare":
                category_multiplier = 25  # 25x boost for rare (was 5x)
            else:
                category_multiplier = 1   # Normal weight for common
            
            final_weight = base_weight * availability_boost * category_multiplier
            
            # Add multiple copies based on weight for selection
            for _ in range(int(final_weight)):
                weighted_prizes.append(prize)
        
        if weighted_prizes:
            selected = random.choice(weighted_prizes)
            logger.debug(f"Weighted selection from {len(prizes)} {category} items: {selected['name']} "
                        f"(weight factor: {len([p for p in weighted_prizes if p['name'] == selected['name']])}/{len(weighted_prizes)})")
            # 🔧 FIX: Convert SQLite Row to dict for JSON serialization
            if hasattr(selected, 'keys'):
                selected = dict(selected)
            return selected
        
        fallback = random.choice(prizes)
        # 🔧 FIX: Convert SQLite Row to dict for JSON serialization
        if hasattr(fallback, 'keys'):
            fallback = dict(fallback)
        return fallback
    
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
        
        # 🔧 DEBUG: Check selected_prize object type and content
        logger.info(f"🔍 DEBUG selected_prize type: {type(selected_prize)}")
        logger.info(f"🔍 DEBUG selected_prize keys: {list(selected_prize.keys()) if hasattr(selected_prize, 'keys') else 'No keys method'}")
        logger.info(f"🔍 DEBUG selected_prize dict conversion: {dict(selected_prize) if hasattr(selected_prize, 'keys') else selected_prize}")
        
        # 🔧 ENSURE CONVERSION: Force conversion to regular dict
        if hasattr(selected_prize, 'keys'):
            selected_prize = dict(selected_prize)
            logger.info(f"🔧 Converted to dict: {selected_prize}")
        
        # Verify the mapping is correct using ID
        if all_wheel_prizes[target_segment_index]['id'] != selected_prize['id']:
            logger.error(f"❌ MAPPING ERROR: Selected prize ID {selected_prize['id']} does not match wheel segment {target_segment_index} prize ID {all_wheel_prizes[target_segment_index]['id']}")
            return jsonify({'success': False, 'error': 'Prize mapping error'}), 500
        
        # 🔧 FINAL FIX: Create a clean response object
        response_data = {
            'success': True,
            'selected_prize': {
                'id': selected_prize['id'],
                'name': selected_prize['name'],
                'category': selected_prize['category'],
                'quantity': selected_prize['quantity'],
                'daily_limit': selected_prize['daily_limit'],
                'emoji': selected_prize['emoji'],
                'remaining_quantity': selected_prize['remaining_quantity'],
                'wins_today': selected_prize.get('wins_today', 0)
            },
            'target_segment_index': target_segment_index,
            'total_segments': len(all_wheel_prizes),
            'debug_info': {
                'selected_prize_id': selected_prize['id'],
                'selected_prize_name': selected_prize['name'],
                'all_prize_ids': [p['id'] for p in all_wheel_prizes],
                'all_prize_names': [p['name'] for p in all_wheel_prizes],
                'mapping': [(i, p['id'], p['name']) for i, p in enumerate(all_wheel_prizes)]
            }
        }
        
        logger.info(f"🔧 Final response data: {response_data['selected_prize']}")
        
        return jsonify(response_data)
        
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

# Additional Admin Endpoints for Daily CSV Management

@app.route('/api/admin/reset-database', methods=['POST'])
def admin_reset_database():
    """Admin endpoint to reset database for testing"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        confirm = data.get('confirm', False)
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        if not confirm:
            return jsonify({'success': False, 'error': 'Confirmation required'}), 400
        
        # Reset database
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Clear all tables
        cursor.execute('DELETE FROM daily_transactions')
        cursor.execute('DELETE FROM daily_inventory')  
        cursor.execute('DELETE FROM daily_prizes')
        
        conn.commit()
        conn.close()
        
        logger.info("🔄 Database reset by admin")
        
        return jsonify({
            'success': True,
            'message': 'Database reset successfully',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/regenerate-csvs', methods=['POST'])
def admin_regenerate_csvs():
    """Admin endpoint to regenerate daily CSV files from itemlist_dates.txt"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        # Import and run the CSV regeneration script
        import subprocess
        import os
        
        script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'update_csvs_from_v2.py')
        result = subprocess.run(['python3', script_path], capture_output=True, text=True, cwd=os.path.dirname(script_path))
        
        if result.returncode == 0:
            logger.info("📊 Daily CSVs regenerated by admin")
            return jsonify({
                'success': True,
                'message': 'Daily CSV files regenerated successfully',
                'output': result.stdout
            })
        else:
            return jsonify({
                'success': False,
                'error': 'CSV regeneration failed',
                'details': result.stderr
            }), 500
        
    except Exception as e:
        logger.error(f"Error regenerating CSVs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/daily-limits-status', methods=['GET'])
def admin_daily_limits_status():
    """Admin endpoint to get current daily limits status"""
    try:
        admin_password = request.args.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get daily limits status
        cursor.execute('''
            SELECT dp.name, dp.category, dp.daily_limit, 
                   COALESCE(today_wins.wins_today, 0) as wins_today,
                   di.remaining_quantity,
                   CASE 
                       WHEN COALESCE(today_wins.wins_today, 0) >= dp.daily_limit THEN 'EXHAUSTED'
                       WHEN di.remaining_quantity <= 0 THEN 'OUT_OF_STOCK'
                       ELSE 'AVAILABLE'
                   END as status
            FROM daily_prizes dp
            JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
            LEFT JOIN (
                SELECT prize_id, COUNT(*) as wins_today
                FROM daily_transactions 
                WHERE date = ? AND transaction_type = 'win'
                GROUP BY prize_id
            ) today_wins ON dp.prize_id = today_wins.prize_id
            WHERE dp.date = ?
            ORDER BY dp.category, dp.name
        ''', (target_date, target_date))
        
        limits_status = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Calculate summary
        summary = {
            'total_items': len(limits_status),
            'available': len([item for item in limits_status if item['status'] == 'AVAILABLE']),
            'exhausted': len([item for item in limits_status if item['status'] == 'EXHAUSTED']),
            'out_of_stock': len([item for item in limits_status if item['status'] == 'OUT_OF_STOCK'])
        }
        
        return jsonify({
            'success': True,
            'date': target_date,
            'limits_status': limits_status,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting daily limits status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/test-selection', methods=['POST'])
def admin_test_selection():
    """Admin endpoint to test the aggressive selection logic"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        test_date = data.get('date', date.today().isoformat())
        num_tests = data.get('num_tests', 5)
        
        # Parse date
        target_date = datetime.fromisoformat(test_date).date()
        
        # Run selection tests
        results = []
        for i in range(num_tests):
            selected_prize = daily_backend.select_prize_with_priority(target_date, f"admin_test_{i}")
            if selected_prize:
                results.append({
                    'test_number': i + 1,
                    'prize_name': selected_prize['name'],
                    'category': selected_prize['category'],
                    'wins_today': selected_prize.get('wins_today', 0),
                    'daily_limit': selected_prize['daily_limit'],
                    'remaining_quantity': selected_prize['remaining_quantity']
                })
            else:
                results.append({
                    'test_number': i + 1,
                    'error': 'No prize selected'
                })
        
        # Calculate category distribution
        categories = {}
        for result in results:
            if 'category' in result:
                category = result['category']
                categories[category] = categories.get(category, 0) + 1
        
        return jsonify({
            'success': True,
            'date': test_date,
            'num_tests': num_tests,
            'results': results,
            'category_distribution': categories
        })
        
    except Exception as e:
        logger.error(f"Error testing selection: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Live Database Editor Endpoints

@app.route('/api/admin/prizes/list', methods=['GET'])
def admin_list_prizes():
    """Admin endpoint to list all prizes for a specific date"""
    try:
        admin_password = request.args.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = request.args.get('date', date.today().isoformat())
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get all prizes for the date with current status
        cursor.execute('''
            SELECT dp.prize_id, dp.name, dp.category, dp.quantity, dp.daily_limit, 
                   dp.available_dates, dp.emoji,
                   di.remaining_quantity,
                   COALESCE(today_wins.wins_today, 0) as wins_today
            FROM daily_prizes dp
            LEFT JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
            LEFT JOIN (
                SELECT prize_id, COUNT(*) as wins_today
                FROM daily_transactions 
                WHERE date = ? AND transaction_type = 'win'
                GROUP BY prize_id
            ) today_wins ON dp.prize_id = today_wins.prize_id
            WHERE dp.date = ?
            ORDER BY dp.prize_id
        ''', (target_date, target_date))
        
        prizes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'date': target_date,
            'prizes': prizes,
            'total_count': len(prizes)
        })
        
    except Exception as e:
        logger.error(f"Error listing prizes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/prizes/update', methods=['POST'])
def admin_update_prize():
    """Admin endpoint to update a specific prize"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        prize_id = data.get('prize_id')
        target_date = data.get('date', date.today().isoformat())
        updates = data.get('updates', {})
        
        if not prize_id or not updates:
            return jsonify({'success': False, 'error': 'Prize ID and updates required'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query for daily_prizes
        prize_updates = []
        prize_values = []
        
        allowed_prize_fields = ['name', 'category', 'quantity', 'daily_limit', 'emoji']
        for field in allowed_prize_fields:
            if field in updates:
                prize_updates.append(f"{field} = ?")
                prize_values.append(updates[field])
        
        if prize_updates:
            prize_values.extend([target_date, prize_id])
            cursor.execute(f'''
                UPDATE daily_prizes 
                SET {', '.join(prize_updates)}
                WHERE date = ? AND prize_id = ?
            ''', prize_values)
        
        # Update inventory if remaining_quantity is provided
        if 'remaining_quantity' in updates:
            cursor.execute('''
                UPDATE daily_inventory 
                SET remaining_quantity = ?
                WHERE date = ? AND prize_id = ?
            ''', (updates['remaining_quantity'], target_date, prize_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🔧 Prize {prize_id} updated by admin: {updates}")
        
        return jsonify({
            'success': True,
            'message': f'Prize {prize_id} updated successfully',
            'updated_fields': list(updates.keys())
        })
        
    except Exception as e:
        logger.error(f"Error updating prize: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/prizes/add', methods=['POST'])
def admin_add_prize():
    """Admin endpoint to add a new prize for a specific date"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = data.get('date', date.today().isoformat())
        prize_data = data.get('prize', {})
        
        required_fields = ['name', 'category', 'quantity', 'daily_limit']
        for field in required_fields:
            if field not in prize_data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get next available prize_id
        cursor.execute('SELECT MAX(prize_id) FROM daily_prizes WHERE date = ?', (target_date,))
        max_id = cursor.fetchone()[0] or 0
        new_prize_id = max_id + 1
        
        # Insert into daily_prizes
        cursor.execute('''
            INSERT INTO daily_prizes (prize_id, name, category, quantity, daily_limit, date, available_dates, emoji)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            new_prize_id,
            prize_data['name'],
            prize_data['category'],
            prize_data['quantity'],
            prize_data['daily_limit'],
            target_date,
            prize_data.get('available_dates', '*'),
            prize_data.get('emoji', '🎁')
        ))
        
        # Insert into daily_inventory
        cursor.execute('''
            INSERT INTO daily_inventory (prize_id, date, name, initial_quantity, remaining_quantity, daily_limit)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (new_prize_id, target_date, prize_data['name'], prize_data['quantity'], prize_data['quantity'], prize_data['daily_limit']))
        
        conn.commit()
        conn.close()
        
        logger.info(f"➕ New prize added by admin: {prize_data['name']} (ID: {new_prize_id})")
        
        return jsonify({
            'success': True,
            'message': f'Prize "{prize_data["name"]}" added successfully',
            'prize_id': new_prize_id
        })
        
    except Exception as e:
        logger.error(f"Error adding prize: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/prizes/delete', methods=['POST'])
def admin_delete_prize():
    """Admin endpoint to delete a prize for a specific date"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        prize_id = data.get('prize_id')
        target_date = data.get('date', date.today().isoformat())
        
        if not prize_id:
            return jsonify({'success': False, 'error': 'Prize ID required'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get prize name for logging
        cursor.execute('SELECT name FROM daily_prizes WHERE date = ? AND prize_id = ?', (target_date, prize_id))
        prize_name = cursor.fetchone()
        prize_name = prize_name[0] if prize_name else f"ID {prize_id}"
        
        # Delete from all tables
        cursor.execute('DELETE FROM daily_transactions WHERE date = ? AND prize_id = ?', (target_date, prize_id))
        cursor.execute('DELETE FROM daily_inventory WHERE date = ? AND prize_id = ?', (target_date, prize_id))
        cursor.execute('DELETE FROM daily_prizes WHERE date = ? AND prize_id = ?', (target_date, prize_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Prize deleted by admin: {prize_name} (ID: {prize_id})")
        
        return jsonify({
            'success': True,
            'message': f'Prize "{prize_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting prize: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/load-daily-csv', methods=['POST'])
def admin_load_daily_csv():
    """Admin endpoint to load prizes directly from daily CSV file"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = data.get('date', date.today().isoformat())
        
        # Load prizes from CSV for this date
        csv_dir = os.path.join(os.path.dirname(__file__), '..', 'daily_csvs')
        prize_manager_instance = DailyPrizeManager(csv_dir, db_manager)
        success = prize_manager_instance.sync_all_items_to_database(datetime.fromisoformat(target_date).date())
        
        if success:
            logger.info(f"📊 Daily CSV loaded by admin for {target_date}")
            return jsonify({
                'success': True,
                'message': f'Daily CSV loaded successfully for {target_date}',
                'date': target_date
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to load daily CSV for {target_date}'
            }), 500
        
    except Exception as e:
        logger.error(f"Error loading daily CSV: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/validate-itemlist', methods=['POST'])
def admin_validate_itemlist():
    """Admin endpoint to validate itemlist_dates_v2.txt format"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        # Try to find itemlist_dates_v2.txt
        import os
        possible_paths = [
            'itemlist_dates_v2.txt',
            '/app/itemlist_dates_v2.txt',
            os.path.join(os.path.dirname(__file__), '..', 'itemlist_dates_v2.txt')
        ]
        
        itemlist_file = None
        for path in possible_paths:
            if os.path.exists(path):
                itemlist_file = path
                break
        
        if not itemlist_file:
            return jsonify({
                'success': False,
                'error': 'itemlist_dates_v2.txt not found',
                'searched_paths': possible_paths
            }), 404
        
        # Validate format
        validation_results = {
            'file_path': itemlist_file,
            'total_lines': 0,
            'valid_items': 0,
            'invalid_items': 0,
            'categories': {'common': 0, 'rare': 0, 'ultra_rare': 0},
            'errors': [],
            'warnings': [],
            'sample_items': []
        }
        
        with open(itemlist_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                validation_results['total_lines'] += 1
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                try:
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) < 6:
                        validation_results['errors'].append(f"Line {line_num}: Insufficient columns (need at least 6)")
                        validation_results['invalid_items'] += 1
                        continue
                    
                    # Validate required fields
                    item_id = int(parts[0])
                    name = parts[1]
                    category = parts[2].lower()
                    quantity = int(parts[3])
                    daily_limit = int(parts[4])
                    available_dates = parts[5]
                    emoji = parts[6] if len(parts) > 6 else '🎁'
                    
                    # Validate category
                    if category not in ['common', 'rare', 'ultra_rare']:
                        validation_results['errors'].append(f"Line {line_num}: Invalid category '{category}' (must be common, rare, or ultra_rare)")
                        validation_results['invalid_items'] += 1
                        continue
                    
                    # Validate quantities
                    if quantity <= 0 or daily_limit <= 0:
                        validation_results['errors'].append(f"Line {line_num}: Quantity and daily_limit must be > 0")
                        validation_results['invalid_items'] += 1
                        continue
                    
                    # Validate available_dates format
                    if available_dates != '*' and '|' in available_dates:
                        # Check date format
                        dates = available_dates.split('|')
                        for date_str in dates:
                            try:
                                datetime.strptime(date_str, '%Y-%m-%d')
                            except ValueError:
                                validation_results['warnings'].append(f"Line {line_num}: Invalid date format '{date_str}' (should be YYYY-MM-DD)")
                    
                    # Valid item
                    validation_results['valid_items'] += 1
                    validation_results['categories'][category] += 1
                    
                    # Add to sample (first 3 of each category)
                    if len([item for item in validation_results['sample_items'] if item['category'] == category]) < 3:
                        validation_results['sample_items'].append({
                            'id': item_id,
                            'name': name,
                            'category': category,
                            'quantity': quantity,
                            'daily_limit': daily_limit,
                            'emoji': emoji
                        })
                    
                except (ValueError, IndexError) as e:
                    validation_results['errors'].append(f"Line {line_num}: Parse error - {str(e)}")
                    validation_results['invalid_items'] += 1
        
        # Generate summary
        is_valid = validation_results['invalid_items'] == 0
        
        return jsonify({
            'success': True,
            'is_valid': is_valid,
            'validation_results': validation_results,
            'summary': {
                'total_items': validation_results['valid_items'],
                'error_count': len(validation_results['errors']),
                'warning_count': len(validation_results['warnings']),
                'categories': validation_results['categories']
            }
        })
        
    except Exception as e:
        logger.error(f"Error validating itemlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/sync-all-dates', methods=['POST'])
def admin_sync_all_dates():
    """🗓️ Admin endpoint to sync ALL dates from itemlist_dates_v2.txt"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        logger.info("🗓️ Admin triggered multi-date sync")
        
        # Create prize manager instance
        csv_dir = os.path.join(os.path.dirname(__file__), '..', 'daily_csvs')
        prize_manager_instance = DailyPrizeManager(csv_dir, db_manager)
        
        # Sync all dates
        success = prize_manager_instance.sync_all_dates_to_database()
        
        if success:
            # Get statistics
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Count total dates and prizes
            cursor.execute('SELECT COUNT(DISTINCT date) as total_dates FROM daily_prizes')
            total_dates = cursor.fetchone()['total_dates']
            
            cursor.execute('SELECT COUNT(*) as total_records FROM daily_prizes')
            total_records = cursor.fetchone()['total_records']
            
            # Get date range
            cursor.execute('SELECT MIN(date) as min_date, MAX(date) as max_date FROM daily_prizes')
            date_range = cursor.fetchone()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'All dates synced successfully',
                'statistics': {
                    'total_dates': total_dates,
                    'total_records': total_records,
                    'date_range': {
                        'start': date_range['min_date'],
                        'end': date_range['max_date']
                    }
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to sync all dates'}), 500
            
    except Exception as e:
        logger.error(f"Error in multi-date sync: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/adjust-quantity', methods=['POST'])
def admin_adjust_quantity():
    """🎛️ Admin endpoint to adjust prize quantities in real-time"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        prize_id = data.get('prize_id')
        adjustment = data.get('adjustment', 0)  # +1, -1, etc.
        target_date = data.get('date', date.today().isoformat())
        
        if not prize_id:
            return jsonify({'success': False, 'error': 'Prize ID required'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current quantity
            cursor.execute('''
                SELECT remaining_quantity, name FROM daily_inventory 
                WHERE date = ? AND prize_id = ?
            ''', (target_date, prize_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Prize not found for this date'}), 404
            
            current_qty = result['remaining_quantity']
            prize_name = result['name']
            new_qty = max(0, current_qty + adjustment)  # Don't allow negative
            
            # Update quantity
            cursor.execute('''
                UPDATE daily_inventory 
                SET remaining_quantity = ?
                WHERE date = ? AND prize_id = ?
            ''', (new_qty, target_date, prize_id))
            
            # Log the adjustment
            cursor.execute('''
                INSERT INTO daily_transactions (date, prize_id, name, user_identifier, transaction_type, quantity)
                VALUES (?, ?, ?, 'ADMIN_ADJUSTMENT', 'adjustment', ?)
            ''', (target_date, prize_id, prize_name, adjustment))
            
            conn.commit()
            
            logger.info(f"📊 Admin adjusted {prize_name} quantity: {current_qty} → {new_qty} (adjustment: {adjustment:+d})")
            
            return jsonify({
                'success': True,
                'prize_name': prize_name,
                'old_quantity': current_qty,
                'new_quantity': new_qty,
                'adjustment': adjustment
            })
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adjusting quantity: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error in quantity adjustment: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/set-quantity', methods=['POST'])
def admin_set_quantity():
    """🎯 Admin endpoint to set exact prize quantity"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        prize_id = data.get('prize_id')
        new_quantity = data.get('quantity', 0)
        target_date = data.get('date', date.today().isoformat())
        
        if not prize_id or new_quantity < 0:
            return jsonify({'success': False, 'error': 'Valid prize ID and non-negative quantity required'}), 400
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current quantity
            cursor.execute('''
                SELECT remaining_quantity, name FROM daily_inventory 
                WHERE date = ? AND prize_id = ?
            ''', (target_date, prize_id))
            
            result = cursor.fetchone()
            if not result:
                return jsonify({'success': False, 'error': 'Prize not found for this date'}), 404
            
            old_quantity = result['remaining_quantity']
            prize_name = result['name']
            
            # Update quantity
            cursor.execute('''
                UPDATE daily_inventory 
                SET remaining_quantity = ?
                WHERE date = ? AND prize_id = ?
            ''', (new_quantity, target_date, prize_id))
            
            # Log the change
            cursor.execute('''
                INSERT INTO daily_transactions (date, prize_id, name, user_identifier, transaction_type, quantity)
                VALUES (?, ?, ?, 'ADMIN_SET', 'set_quantity', ?)
            ''', (target_date, prize_id, prize_name, new_quantity - old_quantity))
            
            conn.commit()
            
            logger.info(f"📊 Admin set {prize_name} quantity: {old_quantity} → {new_quantity}")
            
            return jsonify({
                'success': True,
                'prize_name': prize_name,
                'old_quantity': old_quantity,
                'new_quantity': new_quantity
            })
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error setting quantity: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
    
    except Exception as e:
        logger.error(f"Error in set quantity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 🏗️ IMPROVED ARCHITECTURE: Database-First with CSV Export/Import
@app.route('/api/admin/export-date-to-csv', methods=['POST'])
def admin_export_date_to_csv():
    """📤 Export database state to CSV file (Database → CSV)"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = data.get('date', date.today().isoformat())
        
        logger.info(f"📤 Exporting database state to CSV for {target_date}")
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current database state with all details
            cursor.execute('''
                SELECT dp.prize_id as id, dp.name, dp.category, 
                       di.remaining_quantity as quantity, dp.daily_limit, 
                       dp.emoji, dp.available_dates,
                       COALESCE(wins.wins_today, 0) as wins_today
                FROM daily_prizes dp
                JOIN daily_inventory di ON dp.date = di.date AND dp.prize_id = di.prize_id
                LEFT JOIN (
                    SELECT prize_id, COUNT(*) as wins_today
                    FROM daily_transactions 
                    WHERE date = ? AND transaction_type = 'win'
                    GROUP BY prize_id
                ) wins ON dp.prize_id = wins.prize_id
                WHERE dp.date = ?
                ORDER BY dp.prize_id
            ''', (target_date, target_date))
            
            db_data = cursor.fetchall()
            
            if not db_data:
                return jsonify({'success': False, 'error': f'No data found in database for {target_date}'}), 404
            
            # Prepare CSV content
            csv_content = "id,name,category,quantity,daily_limit,emoji,wins_today\n"
            for row in db_data:
                csv_content += f"{row['id']},{row['name']},{row['category']},{row['quantity']},{row['daily_limit']},{row['emoji'] or '🎁'},{row['wins_today']}\n"
            
            logger.info(f"✅ Generated CSV content for {len(db_data)} records")
            
            return jsonify({
                'success': True,
                'message': f'Database exported to CSV for {target_date}',
                'csv_content': csv_content,
                'records_exported': len(db_data),
                'date': target_date
            })
            
        except Exception as e:
            logger.error(f"Error exporting database to CSV: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in database to CSV export: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/reload-from-master-config', methods=['POST'])
def admin_reload_from_master_config():
    """🔄 Reload database from master config (itemlist_dates_v2.txt → Database)"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        target_date = data.get('date')
        reload_all_dates = data.get('reload_all_dates', False)
        
        logger.info(f"🔄 Reloading from master config - Date: {target_date}, All dates: {reload_all_dates}")
        
        # Create prize manager instance
        csv_dir = os.path.join(os.path.dirname(__file__), '..', 'daily_csvs')
        prize_manager_instance = DailyPrizeManager(csv_dir, db_manager)
        
        if reload_all_dates:
            # Reload all dates from master config
            success = prize_manager_instance.sync_all_dates_to_database()
            
            if success:
                # Get statistics
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(DISTINCT date) as total_dates FROM daily_prizes')
                total_dates = cursor.fetchone()['total_dates']
                
                cursor.execute('SELECT MIN(date) as min_date, MAX(date) as max_date FROM daily_prizes')
                date_range = cursor.fetchone()
                
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'All dates reloaded from master config',
                    'total_dates': total_dates,
                    'date_range': {
                        'start': date_range['min_date'],
                        'end': date_range['max_date']
                    }
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to reload all dates'}), 500
        
        else:
            # Reload specific date
            if not target_date:
                target_date = date.today().isoformat()
            
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # Clear existing data for this date
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM daily_prizes WHERE date = ?', (target_date,))
            cursor.execute('DELETE FROM daily_inventory WHERE date = ?', (target_date,))
            conn.commit()
            conn.close()
            
            # Reload from master config
            success = prize_manager_instance.sync_all_items_to_database(target_date_obj)
            
            if success:
                # Get count of reloaded items
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) as count FROM daily_prizes WHERE date = ?', (target_date,))
                count = cursor.fetchone()['count']
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Date {target_date} reloaded from master config',
                    'records_loaded': count,
                    'date': target_date
                })
            else:
                return jsonify({'success': False, 'error': f'Failed to reload {target_date}'}), 500
            
    except Exception as e:
        logger.error(f"Error reloading from master config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/database-status', methods=['GET'])
def admin_database_status():
    """📊 Get comprehensive database status (Database-first architecture)"""
    try:
        admin_password = request.args.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get overall statistics
            cursor.execute('SELECT COUNT(DISTINCT date) as total_dates FROM daily_prizes')
            total_dates = cursor.fetchone()['total_dates']
            
            cursor.execute('SELECT COUNT(*) as total_records FROM daily_prizes')
            total_records = cursor.fetchone()['total_records']
            
            cursor.execute('SELECT MIN(date) as min_date, MAX(date) as max_date FROM daily_prizes')
            date_range = cursor.fetchone()
            
            # Get transaction statistics
            cursor.execute('SELECT COUNT(*) as total_transactions FROM daily_transactions')
            total_transactions = cursor.fetchone()['total_transactions']
            
            cursor.execute('''
                SELECT COUNT(DISTINCT user_identifier) as unique_users 
                FROM daily_transactions 
                WHERE transaction_type = 'win'
            ''')
            unique_users = cursor.fetchone()['unique_users']
            
            # Get recent activity
            cursor.execute('''
                SELECT date, COUNT(*) as daily_wins
                FROM daily_transactions 
                WHERE transaction_type = 'win'
                GROUP BY date
                ORDER BY date DESC
                LIMIT 7
            ''')
            recent_activity = [dict(row) for row in cursor.fetchall()]
            
            # Get category distribution
            cursor.execute('''
                SELECT category, COUNT(*) as count, SUM(quantity) as total_quantity
                FROM daily_prizes
                WHERE date = ?
                GROUP BY category
            ''', (date.today().isoformat(),))
            category_stats = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'success': True,
                'database_status': {
                    'total_dates': total_dates,
                    'total_records': total_records,
                    'date_range': {
                        'start': date_range['min_date'],
                        'end': date_range['max_date']
                    },
                    'transactions': {
                        'total_transactions': total_transactions,
                        'unique_users': unique_users
                    },
                    'recent_activity': recent_activity,
                    'category_stats': category_stats
                }
            })
            
        except Exception as e:
            logger.error(f"Error getting database status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in database status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/daily-prizes-log', methods=['GET'])
def get_daily_prizes_log():
    """📋 Get today's prizes won with timestamps for display table"""
    try:
        # Get target date (default to today)
        target_date = request.args.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        date_str = target_date.isoformat()
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Get today's won prizes with details
        cursor.execute('''
            SELECT dt.prize_id, dt.name, dt.user_identifier, dt.timestamp,
                   dp.category, dp.emoji
            FROM daily_transactions dt
            JOIN daily_prizes dp ON dt.prize_id = dp.prize_id AND dt.date = dp.date
            WHERE dt.date = ? AND dt.transaction_type = 'win'
            ORDER BY dt.timestamp DESC
        ''', (date_str,))
        
        transactions = []
        for row in cursor.fetchall():
            # Format timestamp for display
            timestamp_obj = datetime.fromisoformat(row['timestamp'])
            formatted_time = timestamp_obj.strftime('%H:%M:%S')
            
            transactions.append({
                'prize_id': row['prize_id'],
                'name': row['name'],
                'user_identifier': row['user_identifier'][:8] + '...' if len(row['user_identifier']) > 8 else row['user_identifier'],  # Truncate for privacy
                'timestamp': row['timestamp'],
                'formatted_time': formatted_time,
                'category': row['category'],
                'emoji': row['emoji']
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'date': date_str,
            'prizes_won': transactions,
            'total_count': len(transactions)
        })
        
    except Exception as e:
        logger.error(f"Error getting daily prizes log: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/audit-log', methods=['GET'])
def get_audit_log():
    """📊 Get comprehensive audit log of all transactions"""
    try:
        # Get parameters
        date_filter = request.args.get('date')  # Optional date filter
        limit = int(request.args.get('limit', 100))  # Default 100 records
        offset = int(request.args.get('offset', 0))  # For pagination
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Build query based on filters
        where_clause = ""
        params = []
        
        if date_filter:
            where_clause = "WHERE dt.date = ?"
            params.append(date_filter)
        
        # Get audit log with all transaction details
        cursor.execute(f'''
            SELECT dt.id, dt.date, dt.prize_id, dt.name, dt.user_identifier, 
                   dt.transaction_type, dt.quantity, dt.timestamp,
                   dp.category, dp.emoji, dp.daily_limit,
                   di.remaining_quantity
            FROM daily_transactions dt
            LEFT JOIN daily_prizes dp ON dt.prize_id = dp.prize_id AND dt.date = dp.date
            LEFT JOIN daily_inventory di ON dt.prize_id = di.prize_id AND dt.date = di.date
            {where_clause}
            ORDER BY dt.timestamp DESC
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        
        audit_entries = []
        for row in cursor.fetchall():
            # Format timestamp
            timestamp_obj = datetime.fromisoformat(row['timestamp'])
            formatted_timestamp = timestamp_obj.strftime('%Y-%m-%d %H:%M:%S')
            
            audit_entries.append({
                'id': row['id'],
                'date': row['date'],
                'prize_id': row['prize_id'],
                'name': row['name'],
                'user_identifier': row['user_identifier'],
                'transaction_type': row['transaction_type'],
                'quantity': row['quantity'],
                'timestamp': row['timestamp'],
                'formatted_timestamp': formatted_timestamp,
                'category': row['category'],
                'emoji': row['emoji'],
                'daily_limit': row['daily_limit'],
                'remaining_quantity': row['remaining_quantity']
            })
        
        # Get total count for pagination
        cursor.execute(f'''
            SELECT COUNT(*) as total
            FROM daily_transactions dt
            {where_clause}
        ''', params)
        
        total_count = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'audit_log': audit_entries,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
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
