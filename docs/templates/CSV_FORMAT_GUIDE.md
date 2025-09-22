# Prize Configuration CSV Format Guide

## Overview
This document explains the CSV format used for configuring prizes in the PickerWheel Contest system.

## File Format
The prize configuration file is a CSV (Comma-Separated Values) file with the following columns:

| Column Name | Description | Example Values | Notes |
|-------------|-------------|---------------|-------|
| Item/Combo Name | Name of the prize | "Smart TV 32 inches" | Case-sensitive, must be unique |
| Category | Prize category | "Common", "Rare", "Ultra Rare" | Determines availability and selection probability |
| Total Quantity | Total number of this prize available | "1", "10", "100" | For the entire contest period |
| Daily Limit | Maximum wins per day | "1", "100" | Use higher values (e.g., 100) for common items |
| Emoji | Emoji to represent the prize | "📺", "🎁", "🔋" | Used in UI display |
| Available Dates | Specific dates when prize is available | "2025-10-01\|2025-10-21" | Use "\|" to separate multiple dates, "*" for all dates |
| Description | Description of the prize | "32-inch smart LED TV" | Used in prize display |

## Category Guidelines

### Common Items
- Set `Total Quantity` to 100
- Set `Daily Limit` to 100
- Set `Available Dates` to "*" (available every day)
- These items should always be available

### Rare Items
- Set `Total Quantity` to a moderate number (2-10)
- Set `Daily Limit` to 1
- Can be available on all dates or specific dates

### Ultra Rare Items
- Set `Total Quantity` to a low number (1-3)
- Set `Daily Limit` to 1
- Should only be available on specific dates

## Special Values

### Available Dates
- Use "*" to indicate the prize is available on all dates
- Use pipe-separated dates (e.g., "2025-10-01|2025-10-21") for specific availability
- Dates must be in YYYY-MM-DD format

### Comments
- Lines starting with "#" are treated as comments and ignored

## Example

```csv
Item/Combo Name,Category,Total Quantity,Daily Limit,Emoji,Available Dates,Description
Smart TV 32 inches,Ultra Rare,1,1,📺,2025-10-20,32-inch smart LED TV
Silver Coin,Ultra Rare,2,1,🪙,2025-09-22|2025-10-01|2025-10-21,999 Silver commemorative coin
Smartwatch + Mini Cooler,Common,100,100,⌚,*,Combo pack with smartwatch and mini cooler
```

## Best Practices

1. **Group by Category**: Keep items of the same category together for better readability
2. **Use Comments**: Add comments with "#" to organize sections
3. **Be Consistent**: Use consistent naming and formatting
4. **Validate**: Always validate the CSV file before deploying to production
5. **Backup**: Create backups before making changes

## Troubleshooting

If prizes are not appearing as expected:

1. Check that dates are in the correct format (YYYY-MM-DD)
2. Verify that pipe symbols (|) are used to separate multiple dates
3. Ensure the prize name matches exactly in the database
4. Check that categories are spelled correctly ("Common", "Rare", "Ultra Rare")
5. Verify that daily limits are appropriate for the category
