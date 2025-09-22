#!/usr/bin/env python3
"""
CSV Format Converter for PickerWheel Contest

This script converts the old CSV format to the new format.
"""

import csv
import os
import sys
from datetime import datetime

def convert_csv_format(input_file, output_file):
    """Convert old CSV format to new format"""
    
    # Column mapping from old to new
    column_mapping = {
        'Item/Combo List': 'Item/Combo Name',
        'Category': 'Category',
        'Quantity': 'Total Quantity',
        'Quantity Per Day': 'Daily Limit',
        'Available Dates': 'Available Dates'
    }
    
    # New columns to add
    new_columns = ['Emoji', 'Description']
    
    # Read input file
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        rows = list(reader)
    
    # Get emoji for each item
    emoji_map = {
        'smart tv': '📺',
        'silver coin': '🪙',
        'refrigerator': '❄️',
        'washing machine': '🧺',
        'aircooler': '❄️',
        'air cooler': '❄️',
        'soundbar': '🎼',
        'dinner set': '🍽️',
        'jio tab': '📱',
        'home theatre': '🔊',
        'speaker': '🔈',
        'gas stove': '🔥',
        'mixer': '🥤',
        'mobile': '📱',
        'smartphone': '📱',
        'smartwatch': '⌚',
        'cooler': '❄️',
        'power bank': '🔋',
        'neckband': '🎧',
        'luggage': '🧳',
        'pressure cooker': '🍲',
        'pouch': '📱',
        'screen guard': '📱',
        'trimmer': '✂️',
        'earphones': '🎧'
    }
    
    # Generate descriptions
    def generate_description(item, category):
        """Generate a description based on the item name and category"""
        category_prefix = category.replace('_', ' ').title()
        
        if '+' in item:
            return f"{category_prefix} combo pack: {item}"
        else:
            return f"{category_prefix} prize: {item}"
    
    # Find best emoji for an item
    def find_emoji(item_name):
        """Find the best emoji for an item based on its name"""
        item_lower = item_name.lower()
        
        for key, emoji in emoji_map.items():
            if key in item_lower:
                return emoji
        
        # Default emoji if no match
        return '🎁'
    
    # Create output rows with new format
    output_rows = []
    
    # Add header comment
    output_rows.append("# Prize Configuration - Generated on " + datetime.now().strftime("%Y-%m-%d"))
    output_rows.append("# Format: Item/Combo Name,Category,Total Quantity,Daily Limit,Emoji,Available Dates,Description")
    output_rows.append("")
    
    # Group items by category
    items_by_category = {'common': [], 'rare': [], 'ultra_rare': [], 'ultra rare': []}
    
    for row in rows:
        category = row['Category'].strip().lower().replace(' ', '_')
        if category in items_by_category:
            items_by_category[category].append(row)
        else:
            # Default to common if category not recognized
            items_by_category['common'].append(row)
    
    # Create new rows with category headers
    for category, items in [('common', 'Common Items (High Availability)'), 
                           ('rare', 'Rare Items (Limited Availability)'),
                           ('ultra_rare', 'Ultra Rare Items (Very Limited Availability)'),
                           ('ultra rare', 'Ultra Rare Items (Very Limited Availability)')]:
        
        if items_by_category[category]:
            output_rows.append(f"# {items}")
            
            for row in items_by_category[category]:
                new_row = {}
                
                # Map old columns to new columns
                for old_col, new_col in column_mapping.items():
                    if old_col in row:
                        new_row[new_col] = row[old_col]
                
                # Add new columns
                item_name = row['Item/Combo List'].strip()
                category_name = row['Category'].strip()
                
                new_row['Emoji'] = find_emoji(item_name)
                new_row['Description'] = generate_description(item_name, category_name.lower())
                
                output_rows.append(new_row)
            
            # Add empty line between categories
            output_rows.append({})
    
    # Write output file
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        # First write the comment lines
        outfile.write("# Prize Configuration - Generated on " + datetime.now().strftime("%Y-%m-%d") + "\n")
        outfile.write("# Format: Item/Combo Name,Category,Total Quantity,Daily Limit,Emoji,Available Dates,Description\n")
        outfile.write("\n")
        
        # Then write the actual CSV data
        fieldnames = list(column_mapping.values()) + new_columns
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Group items by category
        categories = {
            'common': {'title': '# Common Items (High Availability)', 'items': []},
            'rare': {'title': '# Rare Items (Limited Availability)', 'items': []},
            'ultra_rare': {'title': '# Ultra Rare Items (Very Limited Availability)', 'items': []},
            'ultra rare': {'title': '# Ultra Rare Items (Very Limited Availability)', 'items': []}
        }
        
        # Group items by category
        for row in rows:
            category = row['Category'].strip().lower().replace(' ', '_')
            
            new_row = {}
            # Map old columns to new columns
            for old_col, new_col in column_mapping.items():
                if old_col in row:
                    new_row[new_col] = row[old_col]
            
            # Add new columns
            item_name = row['Item/Combo List'].strip()
            category_name = row['Category'].strip()
            
            new_row['Emoji'] = find_emoji(item_name)
            new_row['Description'] = generate_description(item_name, category_name.lower())
            
            # Add to appropriate category
            if category in categories:
                categories[category]['items'].append(new_row)
            else:
                # Default to common if category not recognized
                categories['common']['items'].append(new_row)
        
        # Write categories in order
        for category_key in ['common', 'rare', 'ultra_rare', 'ultra rare']:
            category = categories[category_key]
            if category['items']:
                # Write category header as a comment row
                outfile.write("\n" + category['title'] + "\n")
                
                # Write items in this category
                for item in category['items']:
                    writer.writerow(item)
                
                # Add empty line after category
                outfile.write("\n")
    
    print(f"Converted {len(rows)} items to new format in {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python convert_csv_format.py input_file.csv output_file.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    convert_csv_format(input_file, output_file)
