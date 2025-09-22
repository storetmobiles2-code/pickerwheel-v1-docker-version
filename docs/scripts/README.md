# PickerWheel Scripts

This directory contains scripts for managing and testing the PickerWheel contest system.

## Server Management

- `start-server.sh` - Start the backend server
- `stop-server.sh` - Stop the backend server

## Admin Tools

- `admin/clean_database.py` - Clean up the database to match CSV configuration
- `admin/sync_prizes.py` - Synchronize prizes between CSV and database
- `admin/test_prize_distribution.py` - Test prize distribution and verify daily limits
- `admin/verify_daily_limits.sh` - Verify daily limits for rare and ultra-rare items

## Utility Scripts

- `utils/convert_csv_format.py` - Convert between different CSV formats
- `create_backup.sh` - Create a backup of the entire system

## Maintenance

- `install-deps.sh` - Install dependencies
- `verify-database.sh` - Verify database integrity
- `test-system.sh` - Run system tests
