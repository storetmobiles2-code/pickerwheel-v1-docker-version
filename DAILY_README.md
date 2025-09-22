# Daily PickerWheel Contest Application

A modern, responsive spin wheel contest application that operates on a **daily basis** with complete transactional history and inventory tracking.

## 🎯 Key Features

- **Daily Operation**: Shows ALL items on wheel, awards only available ones
- **Smart Item Management**: Uses `itemlist_dates.txt` for easy item updates
- **Transactional History**: Complete audit trail of all wins
- **Inventory Tracking**: Real-time quantity and daily limit management
- **Priority Logic**: 80% chance to select rare/ultra-rare items when available
- **Interactive Wheel**: Smooth animations with realistic physics
- **Admin Controls**: Password-protected admin panel
- **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd pickerwheel-v1-docker-version
   ```

2. **Start the application**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Main Contest: http://localhost:8082
   - Admin Panel: http://localhost:8082/admin.html

### Manual Setup

1. **Generate daily CSV files**:
   ```bash
   python3 scripts/generate_daily_csv.py
   ```

2. **Start the daily backend**:
   ```bash
   ./scripts/start-server.sh
   ```

3. **Access the application**:
   - Main Contest: http://localhost:9082
   - Admin Panel: http://localhost:9082/admin.html

## 📋 Item Management

### Adding/Updating Items

**Method 1: Direct Edit**
```bash
# Edit the itemlist_dates.txt file directly
nano itemlist_dates.txt
```

**Method 2: Using Management Script**
```bash
# List all items
python3 scripts/manage-itemlist.py list

# Add new item
python3 scripts/manage-itemlist.py add "New Prize" "Common" "50" "10" "*"

# Update existing item
python3 scripts/manage-itemlist.py update 1 name "Updated Prize Name"

# Check availability for specific date
python3 scripts/manage-itemlist.py check 2025-10-02
```

### Item List Format

The `itemlist_dates.txt` file uses this format:
```csv
Item,Category,Quantity,Daily Limit,Available Dates
smartwatch + mini cooler,Common,100,100,*
jio tab,Rare,2,1,2025-10-02|2025-10-07|2025-10-14
Smart TV 32 inches,Ultra Rare,1,1,2025-10-20
```

- **Available Dates**: Use `*` for all days, or specific dates separated by `|`
- **Categories**: Common, Rare, Ultra Rare
- **Daily Limit**: Maximum times this item can be won per day

## 🔧 System Management

### Scripts Available

```bash
# System management
./scripts/start-server.sh          # Start daily backend
./scripts/stop-server.sh           # Stop backend
./scripts/system-status.sh         # Check system status
./scripts/test-daily-system.sh     # Test all functionality

# Item management
python3 scripts/manage-itemlist.py list     # List all items
python3 scripts/manage-itemlist.py add      # Add new item
python3 scripts/manage-itemlist.py update   # Update item
python3 scripts/manage-itemlist.py check    # Check availability

# CSV management
./scripts/manage-daily-csvs.sh status       # Check CSV files
./scripts/manage-daily-csvs.sh generate     # Generate CSV files
./scripts/manage-daily-csvs.sh clean        # Clean old files
```

### Configuration

- **Port**: 9082 (changed from 8080 for testing)
- **Admin Password**: `myTAdmin2025`
- **Database**: SQLite with transactional history
- **Source**: `itemlist_dates.txt` for all items

## 🎮 How It Works

### Daily System Logic

1. **Wheel Display**: Shows ALL 21 items from `itemlist_dates.txt`
2. **Prize Selection**: Only selects from items available for current date
3. **Daily Limits**: Respects daily limits (e.g., 1 ultra-rare item per day)
4. **Priority Logic**: 80% chance to select rare/ultra-rare items when available
5. **Transaction Recording**: Every win is recorded with timestamp and user

### Example Flow

- **Wheel shows**: All 21 items (including unavailable ones)
- **User spins**: System selects from available items only
- **Result**: User wins an available item, inventory is updated
- **History**: Transaction is recorded in database

## 📊 API Endpoints

### Public Endpoints
- `GET /api/prizes/wheel-display` - Get ALL items for wheel display
- `GET /api/prizes/available` - Get available items for today
- `POST /api/pre-spin` - Pre-select available prize
- `POST /api/spin` - Confirm and award prize
- `GET /api/stats` - Get daily statistics

### Admin Endpoints
- `POST /api/admin/load-date` - Load prizes for specific date
- `GET /api/admin/transactions` - Get transaction history
- `POST /api/admin/reset-daily-wins` - Reset daily wins counter

## 🗂️ File Structure

```
├── backend/
│   └── daily_database_backend.py  # Main daily backend
├── frontend/                      # HTML, CSS, JavaScript
├── scripts/                       # Management scripts
│   ├── manage-itemlist.py         # Item management
│   ├── manage-daily-csvs.sh       # CSV management
│   ├── system-status.sh           # System status
│   └── test-daily-system.sh       # System testing
├── daily_csvs/                    # Generated daily CSV files
├── itemlist_dates.txt             # Main item configuration
└── docker-compose.yml             # Docker configuration
```

## 🔍 System Status

Check system status anytime:
```bash
./scripts/system-status.sh
```

This will show:
- Backend status
- Item list status
- Daily CSV files
- Database status
- Quick system test

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting**: Check port 9082 availability
2. **Items not showing**: Verify `itemlist_dates.txt` exists
3. **No available prizes**: Check date availability in item list
4. **Database errors**: Check file permissions

### Logs and Debugging

```bash
# Check backend logs
./scripts/start-server.sh

# Test system functionality
./scripts/test-daily-system.sh

# Check system status
./scripts/system-status.sh
```

## 📈 Benefits of Daily System

- **Decluttered**: Only loads relevant daily data
- **User-Friendly**: Easy item management via text file
- **Audit Trail**: Complete transaction history
- **Flexible**: Easy to add/remove items
- **Fair**: Priority logic ensures rare items are won when available
- **Scalable**: Database-backed with proper inventory tracking

## 🚀 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Manual Deployment
1. Generate daily CSV files
2. Start daily backend
3. Configure web server
4. Set up SSL certificates

## 📝 License

This project is licensed under the MIT License.
