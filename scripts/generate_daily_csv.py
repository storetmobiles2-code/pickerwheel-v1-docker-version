#!/usr/bin/env python3
"""
Daily CSV Generator for PickerWheel Contest
Generates daily CSV files from itemlist_dates.txt for each day until Oct 30, 2025
"""

import csv
import os
from datetime import datetime, date, timedelta
from typing import List, Dict

class DailyCSVGenerator:
    def __init__(self, itemlist_path: str, output_dir: str = "daily_csvs"):
        self.itemlist_path = itemlist_path
        self.output_dir = output_dir
        self.items = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
    def load_items(self):
        """Load items from itemlist_dates.txt"""
        self.items = []
        
        with open(self.itemlist_path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip() and not line.strip().startswith('#')]
            
            # Skip header line
            if lines and lines[0].startswith('Item,'):
                lines = lines[1:]
            
            for line in lines:
                if not line:
                    continue
                    
                parts = line.split(',')
                if len(parts) >= 5:
                    item_name = parts[0].strip()
                    category = parts[1].strip()
                    quantity = parts[2].strip()
                    daily_limit = parts[3].strip()
                    available_dates = parts[4].strip()
                    
                    self.items.append({
                        'name': item_name,
                        'category': category,
                        'quantity': quantity,
                        'daily_limit': daily_limit,
                        'available_dates': available_dates
                    })
        
        print(f"Loaded {len(self.items)} items from {self.itemlist_path}")
    
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
    
    def generate_daily_csv(self, target_date: date) -> str:
        """Generate CSV for a specific date"""
        date_str = target_date.isoformat()
        filename = f"prizes_{date_str}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        # Filter items available on this date
        available_items = []
        for item in self.items:
            if self.is_item_available_on_date(item, target_date):
                available_items.append(item)
        
        # Write CSV file
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Item', 'Category', 'Quantity', 'Daily Limit', 'Available Dates']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for item in available_items:
                writer.writerow({
                    'Item': item['name'],
                    'Category': item['category'],
                    'Quantity': item['quantity'],
                    'Daily Limit': item['daily_limit'],
                    'Available Dates': date_str  # Set to specific date
                })
        
        print(f"Generated {filename} with {len(available_items)} items")
        return filepath
    
    def generate_all_daily_csvs(self, start_date: date = None, end_date: date = None):
        """Generate CSV files for all days from start_date to end_date"""
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = date(2025, 10, 30)  # Default to Oct 30, 2025
        
        current_date = start_date
        generated_files = []
        
        print(f"Generating daily CSV files from {start_date} to {end_date}")
        
        while current_date <= end_date:
            filepath = self.generate_daily_csv(current_date)
            generated_files.append(filepath)
            current_date += timedelta(days=1)
        
        print(f"Generated {len(generated_files)} daily CSV files")
        return generated_files
    
    def get_daily_summary(self, target_date: date) -> Dict:
        """Get summary of items available on a specific date"""
        available_items = []
        category_counts = {'Common': 0, 'Rare': 0, 'Ultra Rare': 0}
        
        for item in self.items:
            if self.is_item_available_on_date(item, target_date):
                available_items.append(item)
                category_counts[item['category']] += 1
        
        return {
            'date': target_date.isoformat(),
            'total_items': len(available_items),
            'category_breakdown': category_counts,
            'items': available_items
        }

def main():
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    itemlist_path = os.path.join(project_root, 'itemlist_dates.txt')
    output_dir = os.path.join(project_root, 'daily_csvs')
    
    print(f"Script directory: {script_dir}")
    print(f"Project root: {project_root}")
    print(f"Itemlist path: {itemlist_path}")
    print(f"Output directory: {output_dir}")
    
    # Check if itemlist file exists
    if not os.path.exists(itemlist_path):
        print(f"Error: {itemlist_path} not found!")
        return
    
    # Initialize generator
    generator = DailyCSVGenerator(itemlist_path, output_dir)
    
    # Load items
    generator.load_items()
    
    # Generate daily CSV files from today to Oct 30, 2025
    start_date = date.today()
    end_date = date(2025, 10, 30)
    
    generated_files = generator.generate_all_daily_csvs(start_date, end_date)
    
    # Show summary for today
    today_summary = generator.get_daily_summary(date.today())
    print(f"\nToday's summary ({today_summary['date']}):")
    print(f"  Total items: {today_summary['total_items']}")
    print(f"  Common: {today_summary['category_breakdown']['Common']}")
    print(f"  Rare: {today_summary['category_breakdown']['Rare']}")
    print(f"  Ultra Rare: {today_summary['category_breakdown']['Ultra Rare']}")
    
    # Show summary for a few specific dates
    test_dates = [
        date(2025, 10, 2),
        date(2025, 10, 20),
        date(2025, 10, 21)
    ]
    
    print(f"\nSample date summaries:")
    for test_date in test_dates:
        if test_date <= end_date:
            summary = generator.get_daily_summary(test_date)
            print(f"  {summary['date']}: {summary['total_items']} items "
                  f"(C:{summary['category_breakdown']['Common']}, "
                  f"R:{summary['category_breakdown']['Rare']}, "
                  f"UR:{summary['category_breakdown']['Ultra Rare']})")

if __name__ == "__main__":
    main()
