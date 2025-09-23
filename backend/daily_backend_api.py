#!/usr/bin/env python3
"""
Daily PickerWheel Contest Backend API
Simplified version that loads daily CSV files instead of using database
Created: September 23, 2025
"""

import csv
import json
import logging
import os
import random
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
DAILY_CSV_DIR = '/app/daily_csvs' if os.path.exists('/app') else 'daily_csvs'
PORT = 9082  # Different port for testing
ADMIN_PASSWORD = 'myTAdmin2025'

class DailyPrizeManager:
    """Manages daily prizes from CSV files"""
    
    def __init__(self, csv_dir: str):
        self.csv_dir = csv_dir
        self.current_prizes = []
        self.current_date = None
        self.daily_wins = {}  # Track daily wins per prize
        
    def load_daily_prizes(self, target_date: date = None) -> List[Dict]:
        """Load prizes for a specific date from CSV file"""
        if target_date is None:
            target_date = date.today()
            
        # If we already have prizes for this date, return them
        if self.current_date == target_date and self.current_prizes:
            return self.current_prizes
            
        date_str = target_date.isoformat()
        csv_file = os.path.join(self.csv_dir, f"prizes_{date_str}.csv")
        
        if not os.path.exists(csv_file):
            logger.error(f"Daily CSV file not found: {csv_file}")
            return []
            
        prizes = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for i, row in enumerate(reader):
                    if not row.get('Item', '').strip():
                        continue
                        
                    prize = {
                        'id': i + 1,  # Simple ID based on row number
                        'name': row['Item'].strip(),
                        'category': row['Category'].strip().lower().replace(' ', '_'),
                        'quantity': int(row['Quantity']) if row['Quantity'].isdigit() else 0,
                        'daily_limit': int(row['Daily Limit']) if row['Daily Limit'].isdigit() else 1,
                        'emoji': self._get_emoji_for_prize(row['Item']),
                        'available_date': date_str
                    }
                    prizes.append(prize)
                    
            self.current_prizes = prizes
            self.current_date = target_date
            self.daily_wins = {}  # Reset daily wins for new date
            
            logger.info(f"Loaded {len(prizes)} prizes for {date_str}")
            return prizes
            
        except Exception as e:
            logger.error(f"Error loading daily CSV: {e}")
            return []
    
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
    
    def get_available_prizes(self, target_date: date = None) -> List[Dict]:
        """Get available prizes for a specific date"""
        prizes = self.load_daily_prizes(target_date)
        available_prizes = []
        
        for prize in prizes:
            # Check if prize has reached daily limit
            prize_id = prize['id']
            daily_wins = self.daily_wins.get(prize_id, 0)
            
            if daily_wins < prize['daily_limit']:
                available_prizes.append(prize)
                
        return available_prizes
    
    def select_prize_with_priority(self, target_date: date = None) -> Optional[Dict]:
        """Select a prize with priority for rare/ultra rare items"""
        available_prizes = self.get_available_prizes(target_date)
        
        if not available_prizes:
            return None
            
        # Separate prizes by category
        ultra_rare = [p for p in available_prizes if p['category'] == 'ultra_rare']
        rare = [p for p in available_prizes if p['category'] == 'rare']
        common = [p for p in available_prizes if p['category'] == 'common']
        
        # Priority logic: Ultra Rare > Rare > Common
        # But ensure we don't always pick rare items (add some randomness)
        
        # 70% chance to pick from available rare/ultra rare items
        # 30% chance to pick from common items
        if (ultra_rare or rare) and random.random() < 0.7:
            # Pick from rare/ultra rare items
            if ultra_rare:
                return random.choice(ultra_rare)
            elif rare:
                return random.choice(rare)
        
        # Pick from common items
        if common:
            return random.choice(common)
            
        # Fallback to any available prize
        return random.choice(available_prizes)
    
    def consume_prize(self, prize_id: int) -> bool:
        """Mark a prize as consumed (increment daily wins)"""
        if prize_id not in self.daily_wins:
            self.daily_wins[prize_id] = 0
        self.daily_wins[prize_id] += 1
        return True
    
    def get_daily_stats(self, target_date: date = None) -> Dict:
        """Get daily statistics"""
        if target_date is None:
            target_date = date.today()
            
        available_prizes = self.get_available_prizes(target_date)
        total_prizes = len(self.current_prizes)
        total_wins = sum(self.daily_wins.values())
        
        category_breakdown = {}
        for prize in available_prizes:
            cat = prize['category']
            category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
            
        return {
            'date': target_date.isoformat(),
            'total_prizes': total_prizes,
            'available_prizes': len(available_prizes),
            'total_wins_today': total_wins,
            'category_breakdown': category_breakdown
        }

# Initialize prize manager
prize_manager = DailyPrizeManager(DAILY_CSV_DIR)

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
    """Get all prizes for wheel display (for current date)"""
    try:
        target_date = request.args.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
            
        prizes = prize_manager.load_daily_prizes(target_date)
        
        return jsonify({
            'success': True,
            'prizes': prizes,
            'date': target_date.isoformat()
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

@app.route('/api/spin', methods=['POST'])
def spin_wheel():
    """Handle wheel spin and prize selection"""
    try:
        data = request.get_json() or {}
        user_identifier = data.get('user_id') or request.remote_addr
        
        # Get target date
        target_date = data.get('date')
        if target_date:
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Select prize with priority logic
        selected_prize = prize_manager.select_prize_with_priority(target_date)
        
        if not selected_prize:
            return jsonify({
                'success': False,
                'error': 'No prizes available today'
            }), 400
        
        # Consume the prize
        prize_manager.consume_prize(selected_prize['id'])
        
        # Calculate wheel position (simple mapping)
        available_prizes = prize_manager.get_available_prizes(target_date)
        sector_index = available_prizes.index(selected_prize)
        sector_angle = 360 / len(available_prizes)
        sector_center = sector_index * sector_angle + (sector_angle / 2)
        
        logger.info(f"User {user_identifier} won {selected_prize['name']} on {target_date}")
        
        return jsonify({
            'success': True,
            'prize': selected_prize,
            'sector_index': sector_index,
            'sector_center': sector_center,
            'total_segments': len(available_prizes),
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
        prizes = prize_manager.load_daily_prizes(target_date)
        
        return jsonify({
            'success': True,
            'prizes': prizes,
            'date': target_date.isoformat(),
            'count': len(prizes)
        })
        
    except Exception as e:
        logger.error(f"Error in admin load date: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/admin/reset-daily-wins', methods=['POST'])
def admin_reset_daily_wins():
    """Admin endpoint to reset daily wins counter"""
    try:
        data = request.get_json() or {}
        admin_password = data.get('admin_password')
        
        if admin_password != ADMIN_PASSWORD:
            return jsonify({'success': False, 'error': 'Invalid admin password'}), 401
            
        prize_manager.daily_wins = {}
        
        return jsonify({
            'success': True,
            'message': 'Daily wins counter reset'
        })
        
    except Exception as e:
        logger.error(f"Error resetting daily wins: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Starting Daily PickerWheel Backend on port {PORT}")
    logger.info(f"Daily CSV directory: {DAILY_CSV_DIR}")
    
    # Test loading today's prizes
    try:
        today_prizes = prize_manager.load_daily_prizes(date.today())
        logger.info(f"Loaded {len(today_prizes)} prizes for today")
    except Exception as e:
        logger.error(f"Failed to load today's prizes: {e}")
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
