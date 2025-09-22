# Daily PickerWheel System

## Overview

This is a modified version of the PickerWheel contest application that operates on a **daily basis** instead of loading all data at once. The system uses daily CSV files generated from `itemlist_dates.txt` and maintains transactional history and inventory tracking through a SQLite database.

## Key Features

### ✅ Daily Data Management
- **Daily CSV Files**: Automatically generated from `itemlist_dates.txt` for each day until Oct 30, 2025
- **Dynamic Loading**: Backend loads only the prizes available for the current day
- **Date-based Operation**: Each day has its own set of available prizes
- **All Items on Wheel**: Shows ALL prizes on the wheel regardless of availability
- **Smart Selection**: Only awards prizes that are actually available for the day

### ✅ Inventory Tracking
- **Real-time Inventory**: Tracks remaining quantities for each prize
- **Daily Limits**: Enforces daily limits per prize (e.g., 1 ultra-rare item per day)
- **Automatic Deduction**: Inventory is automatically reduced when prizes are won

### ✅ Transactional History
- **Complete Audit Trail**: Every prize win is recorded with timestamp and user
- **Daily Statistics**: Tracks total wins, unique users, and category breakdowns
- **Database Persistence**: All transactions are stored in SQLite database

### ✅ Priority Logic
- **Rare Item Priority**: 80% chance to select rare/ultra-rare items when available
- **Fair Distribution**: Ensures rare items are won when they're available
- **Smart Selection**: Balances between rare items and common items

## System Architecture

```
itemlist_dates.txt → Daily CSV Generator → Daily CSV Files
                                              ↓
Frontend (Port 8082) ← Daily Backend API ← SQLite Database
                                              ↓
                                    Transaction History
                                    Inventory Tracking
                                    Daily Statistics
```

## File Structure

```
├── daily_csvs/                    # Generated daily CSV files
│   ├── prizes_2025-09-23.csv
│   ├── prizes_2025-09-24.csv
│   └── ...
├── backend/
│   ├── daily_database_backend.py  # Main backend with database
│   └── daily_backend_api.py       # Simple backend (no database)
├── scripts/
│   ├── generate_daily_csv.py      # CSV generator script
│   └── test_daily_backend.py      # Test script
└── start-daily-backend.sh         # Startup script
```

## Database Schema

### Tables
- **daily_prizes**: Stores daily prize configurations
- **daily_inventory**: Tracks remaining quantities
- **daily_transactions**: Records all prize wins
- **daily_stats**: Daily statistics and metrics

## Usage

### 1. Generate Daily CSV Files
```bash
python3 scripts/generate_daily_csv.py
```

### 2. Start the Backend
```bash
./start-daily-backend.sh
```

### 3. Access the Application
- **URL**: http://localhost:8082
- **Port**: 8082 (changed from 8080 for testing)

### 4. Docker Deployment
```bash
docker-compose up --build
```

## API Endpoints

### Public Endpoints
- `GET /api/prizes/wheel-display` - Get all prizes for wheel display
- `GET /api/prizes/available` - Get available prizes for today
- `POST /api/spin` - Spin the wheel and win a prize
- `GET /api/stats` - Get daily statistics

### Admin Endpoints
- `POST /api/admin/load-date` - Load prizes for specific date
- `GET /api/admin/transactions` - Get transaction history
- `POST /api/admin/reset-daily-wins` - Reset daily wins counter

## Configuration

### Environment Variables
- `PORT`: Backend port (default: 9082)
- `ADMIN_PASSWORD`: Admin password (default: myTAdmin2025)
- `DAILY_CSV_DIR`: Directory for daily CSV files

### Daily CSV Format
```csv
Item,Category,Quantity,Daily Limit,Available Dates
smartwatch + mini cooler,Common,100,100,2025-10-02
jio tab,Rare,2,1,2025-10-02
Smart TV 32 inches,Ultra Rare,1,1,2025-10-02
```

## Testing

### Run Backend Tests
```bash
python3 scripts/test_daily_backend.py
```

### Test Specific Date
```bash
curl -X POST http://localhost:8082/api/admin/load-date \
  -H "Content-Type: application/json" \
  -d '{"admin_password": "myTAdmin2025", "date": "2025-10-02"}'
```

## Key Improvements

### ✅ Decluttered Application
- **Reduced Data Load**: Only loads prizes for current day
- **Faster Performance**: Smaller dataset improves response times
- **Better Organization**: Daily-based data management

### ✅ Refined Logic
- **Priority System**: Rare items are prioritized when available
- **Daily Limits**: Enforced per-prize daily limits
- **Inventory Management**: Real-time quantity tracking

### ✅ Transactional Integrity
- **Database Backend**: Proper ACID transactions
- **Audit Trail**: Complete history of all activities
- **Data Persistence**: No data loss on restart

## Monitoring

### Daily Statistics
- Total prizes available
- Prizes won today
- Unique users
- Category breakdown

### Transaction History
- All prize wins with timestamps
- User identification
- Prize details

### Inventory Status
- Remaining quantities
- Daily limit status
- Availability by category

## Troubleshooting

### Common Issues

1. **No CSV file for today**
   - Run the CSV generator: `python3 scripts/generate_daily_csv.py`
   - Check if date is within range (until Oct 30, 2025)

2. **Database errors**
   - Check file permissions
   - Ensure SQLite is available
   - Verify database path

3. **Port conflicts**
   - Change port in `daily_database_backend.py`
   - Update Docker configuration
   - Check firewall settings

### Logs
- Backend logs are written to console
- Database operations are logged
- API requests are tracked

## Migration from Original System

The daily system is designed to be a drop-in replacement:

1. **Same Frontend**: No changes to the UI
2. **Same API**: Compatible endpoints
3. **Enhanced Backend**: Better data management
4. **New Features**: Daily limits and priority logic

## Future Enhancements

- **Multi-day Planning**: Advanced scheduling
- **Analytics Dashboard**: Detailed reporting
- **User Management**: Enhanced user tracking
- **Notification System**: Real-time updates
