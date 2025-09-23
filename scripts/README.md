# Scripts Directory - Daily PickerWheel System

This directory contains essential scripts for managing the Daily PickerWheel Contest System.

## 🚀 Core System Scripts

### Server Management
- **`start-server.sh`** - Start the daily backend server on port 9082
- **`stop-server.sh`** - Stop all backend processes and free up ports
- **`system-status.sh`** - Check system status, backend health, and configuration

### Docker Management
- **`docker.sh`** - Comprehensive Docker management script with multiple commands
  ```bash
  ./scripts/docker.sh start       # Build and start Docker container
  ./scripts/docker.sh stop        # Stop and remove Docker container
  ./scripts/docker.sh restart     # Restart Docker container
  ./scripts/docker.sh status      # Check container status
  ./scripts/docker.sh logs        # View container logs
  ./scripts/docker.sh info        # Show system information
  ./scripts/docker.sh test        # Test the running system
  ./scripts/docker.sh clean       # Clean up Docker resources
  ```

## 📊 Data Management Scripts

### Item Management
- **`manage-itemlist.py`** - Python script to manage items in `itemlist_dates.txt`
  ```bash
  python3 scripts/manage-itemlist.py list          # List all items
  python3 scripts/manage-itemlist.py add           # Add new item
  python3 scripts/manage-itemlist.py update        # Update existing item
  python3 scripts/manage-itemlist.py check         # Check availability
  python3 scripts/manage-itemlist.py validate      # Validate itemlist
  ```

### CSV Management
- **`generate_daily_csv.py`** - Generate daily CSV files from itemlist_dates.txt
- **`manage-daily-csvs.sh`** - Shell script to manage daily CSV files
  ```bash
  ./scripts/manage-daily-csvs.sh generate    # Generate CSV files
  ./scripts/manage-daily-csvs.sh status      # Show CSV status
  ./scripts/manage-daily-csvs.sh clean       # Clean old files
  ./scripts/manage-daily-csvs.sh verify      # Verify specific dates
  ```

## 🧪 Testing Scripts

### System Testing
- **`test-daily-system.sh`** - Comprehensive test of the daily system
- **`test_daily_backend.py`** - Python script for backend testing

## 📋 Quick Reference

### Daily Operations
```bash
# Start the system
./scripts/start-server.sh

# Check system status
./scripts/system-status.sh

# Test the system
./scripts/test-daily-system.sh

# Stop the system
./scripts/stop-server.sh
```

### Item Management
```bash
# List all items
python3 scripts/manage-itemlist.py list

# Add new item
python3 scripts/manage-itemlist.py add "New Prize" "Common" "50" "10" "*"

# Check availability for specific date
python3 scripts/manage-itemlist.py check 2025-10-02
```

### Docker Operations
```bash
# Start with Docker
./scripts/docker.sh start

# Check Docker status
./scripts/docker.sh status

# View logs
./scripts/docker.sh logs

# Test the system
./scripts/docker.sh test

# Stop Docker
./scripts/docker.sh stop

# Get system information
./scripts/docker.sh info
```

## 🔧 Configuration

### Ports
- **Backend**: 9082 (for direct server access)
- **Docker**: 8082 (for Docker container access)

### Key Files
- **`itemlist_dates.txt`** - Main item configuration file
- **`daily_csvs/`** - Generated daily CSV files
- **`pickerwheel_contest.db`** - SQLite database for transactions

## 📝 Script Categories

### Essential Scripts (Keep)
- `start-server.sh` - Core server startup
- `stop-server.sh` - Core server shutdown
- `system-status.sh` - System monitoring
- `test-daily-system.sh` - System testing
- `manage-itemlist.py` - Item management
- `generate_daily_csv.py` - CSV generation
- `manage-daily-csvs.sh` - CSV management

### Docker Scripts (Optional)
- `docker.sh` - Comprehensive Docker management (start, stop, restart, status, logs, info, test, clean)

## 🚨 Troubleshooting

### Common Issues
1. **Port conflicts**: Use `./scripts/stop-server.sh` to free up ports
2. **Missing CSV files**: Run `python3 scripts/generate_daily_csv.py`
3. **Backend not responding**: Check with `./scripts/system-status.sh`

### Debug Commands
```bash
# Check system status
./scripts/system-status.sh

# Test system functionality
./scripts/test-daily-system.sh

# View server logs
./scripts/start-server.sh  # Shows startup logs

# Check Docker logs
./scripts/docker.sh logs
```

## 📈 System Architecture

The daily system works as follows:

1. **Item Configuration**: Items defined in `itemlist_dates.txt`
2. **CSV Generation**: Daily CSV files generated from itemlist
3. **Backend Processing**: `daily_database_backend.py` handles requests
4. **Database Storage**: SQLite database for transactions and inventory
5. **Frontend Display**: Shows all items, awards only available ones

## 🔄 Workflow

### Daily Operations
1. Start system: `./scripts/start-server.sh`
2. Check status: `./scripts/system-status.sh`
3. Monitor: Use admin panel or API endpoints
4. Stop system: `./scripts/stop-server.sh`

### Item Updates
1. Edit items: `python3 scripts/manage-itemlist.py list`
2. Add/update: Use management commands
3. Regenerate CSVs: `python3 scripts/generate_daily_csv.py`
4. Restart system: `./scripts/stop-server.sh && ./scripts/start-server.sh`

## 📞 Support

For issues or questions:
1. Check system status: `./scripts/system-status.sh`
2. Run system test: `./scripts/test-daily-system.sh`
3. Check logs: `./scripts/start-server.sh` (shows startup logs)
4. Review documentation: `../DAILY_README.md`