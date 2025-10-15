# 🏗️ Admin Panel Architecture & Data Flow

## Overview

The pickerwheel application uses a **hybrid architecture** that separates **configuration data** (prizes, categories) from **operational data** (spins, wins, inventory). This allows the admin panel to work independently of CSV files for real-time operations.

---

## 📊 Database Tables

### 1. `daily_prizes` - Prize Definitions
```sql
CREATE TABLE daily_prizes (
    id INTEGER PRIMARY KEY,
    date TEXT,
    prize_id INTEGER,
    name TEXT,
    category TEXT,           -- common, rare, ultra_rare
    quantity INTEGER,        -- Initial quantity for the day
    daily_limit INTEGER,     -- Max wins per day
    available_dates TEXT,    -- Which dates this prize is available
    emoji TEXT
)
```
**Purpose**: Defines what prizes exist and their properties for each date.

---

### 2. `daily_inventory` - Real-Time Inventory
```sql
CREATE TABLE daily_inventory (
    id INTEGER PRIMARY KEY,
    date TEXT,
    prize_id INTEGER,
    name TEXT,
    initial_quantity INTEGER,     -- Starting quantity
    remaining_quantity INTEGER,   -- ⭐ LIVE COUNT - decreases with each win
    daily_limit INTEGER
)
```
**Purpose**: Tracks how many of each prize are currently available. Updated in real-time!

---

### 3. `daily_transactions` ⭐ - AUDIT LOG (The Magic!)
```sql
CREATE TABLE daily_transactions (
    id INTEGER PRIMARY KEY,
    date TEXT,
    prize_id INTEGER,
    name TEXT,
    user_identifier TEXT,         -- User's IP address or session ID
    transaction_type TEXT,         -- 'win', 'adjustment', 'set_quantity'
    quantity INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```
**Purpose**: **Complete audit trail** of every spin result, win, and admin adjustment.
- Every time a user spins and wins → NEW ROW INSERTED
- Every time admin adjusts inventory → NEW ROW INSERTED
- **This table is the results log!**

---

### 4. `daily_stats` - Daily Aggregates
```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY,
    date TEXT,
    total_spins INTEGER,
    total_wins INTEGER,
    unique_users INTEGER
)
```
**Purpose**: Summary statistics per day.

---

## 🔄 Data Flow

### **A. Initial Setup (One-Time)**

```
┌──────────────────────────────────────────────┐
│  itemlist_dates.txt (Master Configuration)  │
│  ├─ Common Items                             │
│  ├─ Rare Items (with dates)                  │
│  └─ Quantities, Limits, Emojis               │
└─────────────────┬────────────────────────────┘
                  │
                  ├──> Python Script: validate_and_update_prizes.py
                  │    ├─ Parses itemlist_dates.txt
                  │    ├─ Generates daily_csvs/prizes_YYYY-MM-DD.csv
                  │    └─ Populates database tables
                  │
                  ▼
    ┌─────────────────────────────┐
    │  DATABASE INITIALIZATION     │
    ├─────────────────────────────┤
    │  INSERT INTO daily_prizes    │
    │  INSERT INTO daily_inventory │
    └─────────────────────────────┘
```

### **B. Runtime Operations (User Spins Wheel)**

```
User clicks "SPIN"
       │
       ▼
Frontend: wheel.js
       │
       └──> POST /api/pre-spin
              │
              └──> Backend selects prize using aggressive algorithm
                     │
                     ├─ Checks daily_inventory.remaining_quantity
                     ├─ Checks daily_limit not exceeded
                     └─ Selects prize based on probability weights

User clicks "CLAIM PRIZE"
       │
       ▼
Frontend: wheel.js
       │
       └──> POST /api/spin
              │
              ▼
       Backend: consume_prize() function
              │
              ├──> 1. INSERT INTO daily_transactions ⭐
              │       VALUES (date, prize_id, name, user_ip, 'win', 1)
              │       [RECORDS THE WIN IN AUDIT LOG]
              │
              ├──> 2. UPDATE daily_inventory
              │       SET remaining_quantity = remaining_quantity - 1
              │       [DECREASES AVAILABLE QUANTITY]
              │
              └──> 3. Returns success to frontend
```

### **C. Admin Panel Operations**

```
Admin Opens Panel → admin.html
       │
       ├──> 1. Load Prize Configuration
       │       GET /api/admin/prizes/list
       │       └──> SELECT * FROM daily_prizes WHERE date = ?
       │            └──> Shows: Name, Category, Emoji, Limits
       │
       ├──> 2. Load Current Inventory
       │       GET /api/admin/daily-limits-status
       │       └──> SELECT remaining_quantity FROM daily_inventory
       │            └──> Shows: How many prizes left
       │
       ├──> 3. Load Audit Log (Results Data!) ⭐
       │       GET /api/audit-log?date=YYYY-MM-DD
       │       └──> SELECT * FROM daily_transactions
       │            ORDER BY timestamp DESC
       │            └──> Shows:
       │                 ├─ Who won what prize
       │                 ├─ When (timestamp)
       │                 ├─ User identifier (IP address)
       │                 ├─ Quantity changes
       │                 └─ Admin adjustments
       │
       └──> 4. Live Inventory Control
              POST /api/admin/adjust-quantity
              └──> UPDATE daily_inventory
                   SET remaining_quantity = remaining_quantity + adjustment
                   [PERSISTS ACROSS RESTARTS]
```

---

## 🎯 Key Points

### ✅ **CSV Files are NOT Required at Runtime**
- CSV files (`daily_csvs/prizes_*.csv`) are only used for:
  - Initial database population
  - Bulk imports/exports
  - Master configuration reloading
- **The wheel does NOT read CSV files during operation!**
- All prize data comes from the database

### ✅ **`daily_transactions` Table IS the Results Log**
- Every spin result is recorded here
- Includes:
  - Prize won
  - User identifier (IP address)
  - Timestamp
  - Transaction type (win, adjustment, etc.)
- **Completely independent of CSV files**
- Persists across Docker restarts

### ✅ **Admin Panel Has Real-Time Database Access**
- Can view live inventory
- Can view complete audit log (all wins)
- Can adjust quantities on-the-fly
- Changes persist immediately in database

### ✅ **Data Persistence**
- Database file: `backend/pickerwheel_contest.db`
- SQLite database persists on disk
- Docker volume ensures data survives container restarts
- All transactions logged permanently

---

## 📱 Admin Panel Features

### **1. Audit Log View**
Located in: `frontend/admin.html` → "📊 Audit Log" section

```javascript
// Admin panel loads audit log from database
async function loadAuditLog(dateFilter = null) {
    const response = await fetch('/api/audit-log?date=' + dateFilter);
    const data = await response.json();
    
    // Displays table with:
    // - Timestamp
    // - Prize name
    // - User identifier
    // - Transaction type
    // - Remaining quantity
}
```

**Example Output:**
```
┌────────────────────┬──────────────┬──────────────┬────────────┬──────┐
│ Timestamp          │ Prize        │ User         │ Type       │ Qty  │
├────────────────────┼──────────────┼──────────────┼────────────┼──────┤
│ 2025-10-14 14:23:05│ Boat Watch   │ 192.168.1.10 │ win        │ 1    │
│ 2025-10-14 14:20:12│ Power Bank   │ 192.168.1.15 │ win        │ 1    │
│ 2025-10-14 14:15:30│ Luggage Bag  │ 192.168.1.10 │ win        │ 1    │
└────────────────────┴──────────────┴──────────────┴────────────┴──────┘
```

### **2. Live Inventory Control**
Admin can:
- Click **+** or **-** buttons to adjust quantities in real-time
- Set exact quantities
- Changes save immediately to database
- No need to restart Docker container
- Changes persist across restarts

### **3. Database Status**
Shows:
- Total dates in database
- Total records
- Total transactions (spins/wins)
- Unique users
- Category distribution

---

## 🔍 How to Verify

### Check if audit log is working:
```bash
# 1. Spin the wheel a few times (use frontend)

# 2. Check database directly
cd /Users/wsyed/git/forks/docker/pickerwheel-v1-docker-version
python3 -c "
import sqlite3
conn = sqlite3.connect('backend/pickerwheel_contest.db')
cursor = conn.cursor()

print('=== Recent Transactions ===')
cursor.execute('''
    SELECT timestamp, name, user_identifier, transaction_type 
    FROM daily_transactions 
    ORDER BY timestamp DESC 
    LIMIT 10
''')

for row in cursor.fetchall():
    print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]}')

conn.close()
"

# 3. Or use admin panel:
# Open: http://localhost:8082/admin.html
# Click: "📊 Load Audit Log"
```

---

## 🎓 Summary

**Q: How does the admin panel work if data is loaded from itemlist_dates.txt and CSV?**

**A:** The admin panel does NOT directly read from CSV files. Instead:

1. **CSV files** → Used only for **initial setup** to populate database
2. **Database tables** → Store all operational data:
   - `daily_prizes` = Prize definitions
   - `daily_inventory` = Current quantities (real-time)
   - `daily_transactions` = **AUDIT LOG** (every spin result)
3. **Admin panel** → Reads from **database tables**, not CSVs

**Q: How is results data/log available?**

**A:** Every time someone spins the wheel and wins a prize, the backend:
1. Inserts a row into `daily_transactions` table
2. Records: date, prize, user IP, timestamp, transaction type
3. This table IS the results log!

The admin panel queries this table to show:
- Who won what
- When they won it
- Their user identifier
- Complete history

**This data persists permanently in the database, completely independent of CSV files!**

---

## 📚 Related Files

- **Backend**: `backend/daily_database_backend.py`
  - `consume_prize()` - Records wins to daily_transactions
  - `get_audit_log()` - API endpoint for audit log
  
- **Admin Panel**: `frontend/admin.html`
  - `loadAuditLog()` - Displays transaction history
  - `displayAuditLog()` - Renders audit table
  
- **Database**: `backend/pickerwheel_contest.db`
  - SQLite database file
  - Contains all tables and data
  
- **Master Config**: `itemlist_dates.txt`
  - Source of truth for prize definitions
  - Used to regenerate database when needed

---

**Last Updated:** October 14, 2025


