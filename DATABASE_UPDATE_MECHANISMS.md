# Database Update Mechanisms Report
**Generated:** September 26, 2025

## 1. Overview
The prize wheel system uses a multi-layered approach to manage prize data, with three main components:
1. Master Configuration (`itemlist_dates_v2.txt`)
2. Daily CSV Files
3. SQLite Database

## 2. Update Methods

### A. Load Daily CSV
- **Button:** "📋 Load Daily CSV" in admin panel
- **Endpoint:** `/api/admin/load-daily-csv`
- **Function:** Loads prizes from a specific day's CSV file into the database
- **Process:**
  1. Reads the CSV file for the selected date
  2. Clears existing database entries for that date
  3. Inserts new prize records
  4. Initializes inventory records
  5. Updates daily statistics

### B. Sync All Dates
- **Button:** "🗓️ Sync All Dates" in admin panel
- **Endpoint:** `/api/admin/sync-all-dates`
- **Function:** Syncs all dates from the master configuration
- **Process:**
  1. Reads `itemlist_dates_v2.txt`
  2. Updates database for all configured dates
  3. Maintains data consistency across all tables
  4. Preserves transaction history

## 3. Database Tables

### daily_prizes
```sql
CREATE TABLE daily_prizes (
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
```

### daily_inventory
```sql
CREATE TABLE daily_inventory (
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
```

### daily_transactions
```sql
CREATE TABLE daily_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    prize_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    user_identifier TEXT,
    transaction_type TEXT DEFAULT 'win',
    quantity INTEGER DEFAULT 1,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### daily_stats
```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    total_prizes INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
)
```

## 4. Recommended Update Workflow

1. **Update Master Configuration:**
   - Edit `itemlist_dates_v2.txt`
   - Verify changes

2. **Generate CSV Files:**
   - Run CSV generation script
   - Verify CSV contents

3. **Update Database:**
   - Option 1: Use "Sync All Dates" for full sync
   - Option 2: Use "Load Daily CSV" for specific dates

4. **Verify Changes:**
   - Run validation report
   - Check database contents

## 5. Important Notes

1. **Data Consistency:**
   - Database is the source of truth for current state
   - CSVs serve as initial data source
   - Master config (`itemlist_dates_v2.txt`) is the template

2. **Transaction History:**
   - All prize wins are recorded in `daily_transactions`
   - History is preserved during updates
   - Provides audit trail for verification

3. **Inventory Management:**
   - Real-time tracking of remaining quantities
   - Daily limits enforced by database
   - Automatic updates on prize wins

4. **Error Handling:**
   - Failed updates are rolled back
   - Data integrity is maintained
   - Error messages are logged

---
*Report generated on September 26, 2025*