# 🎯 PickerWheel Contest v4 - Clean System

## Database-Backed 2-Month Event Management

### 🚀 Quick Start

#### Local Deployment

1. **Verify database migration:**
   ```bash
   ./scripts/verify-database.sh
   ```

2. **Install dependencies (if needed):**
   ```bash
   ./scripts/install-deps.sh
   ```

3. **Start the system:**
   ```bash
   ./scripts/start-server.sh
   ```

4. **Access the contest:**
   - **Main Contest**: http://localhost:9080
   - **Admin Panel**: http://localhost:9080/admin.html (Password: `myTAdmin2025`)

5. **Stop the system:**
   ```bash
   ./scripts/stop-server.sh
   ```

#### Docker Deployment

1. **Install Docker and Docker Compose:**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - [Docker Compose](https://docs.docker.com/compose/install/)

2. **Start the Docker container:**
   ```bash
   ./scripts/start-docker.sh
   ```

3. **Access the contest:**
   - **Main Contest**: http://<your-ip-address>:9080
   - **Admin Panel**: http://<your-ip-address>:9080/admin.html (Password: `myTAdmin2025`)

4. **Stop the Docker container:**
   ```bash
   ./scripts/stop-docker.sh
   ```

5. **For detailed Docker instructions:**
   See [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)

6. **Test prize distribution:**
   ```bash
   ./scripts/admin/test_prize_distribution.py
   ```

7. **Verify daily limits:**
   ```bash
   ./scripts/admin/verify_daily_limits.sh
   ```

8. **Create a backup:**
   ```bash
   ./scripts/create_backup.sh
   ```

### 📁 Project Structure

```
pickerwheel-v4-clean/
├── backend/                 # Python Flask API
│   ├── backend-api.py      # Main API server
│   ├── database-schema.sql # Database schema
│   ├── pickerwheel_contest.db # SQLite database
│   └── requirements.txt    # Python dependencies
├── frontend/               # Web interface
│   ├── index.html         # Main contest page
│   ├── wheel.js           # Wheel logic & API integration
│   ├── style.css          # Styling and animations
│   ├── admin.html         # Admin interface
│   ├── prize-manager.html # Prize management interface
│   ├── manifest.json      # PWA manifest
│   └── sw.js              # Service worker
├── assets/                # Static assets
│   ├── images/           # Logos and graphics
│   └── sounds/           # Audio files
├── scripts/              # Scripts and tools
│   ├── start-server.sh   # Start server
│   ├── stop-server.sh    # Stop server
│   ├── create_backup.sh  # Create system backup
│   ├── README.md         # Scripts documentation
│   ├── admin/            # Admin tools
│   │   ├── clean_database.py       # Clean database
│   │   ├── sync_prizes.py          # Sync prizes
│   │   ├── test_prize_distribution.py # Test distribution
│   │   └── verify_daily_limits.sh  # Verify limits
│   └── utils/            # Utility scripts
│       └── convert_csv_format.py   # Convert CSV formats
├── templates/             # CSV templates
│   ├── prize_template.csv # Prize template
│   └── simple_prizes.csv  # Simple prizes template
└── itemlist_dates.txt     # Current prize configuration
```

### 🎁 Prize System

**22 Total Prizes:**
- **Ultra Rare (6)**: Smart TV, Silver Coin, Refrigerator, etc.
- **Rare (8)**: Home appliances and electronics
- **Common (8)**: Combo items and accessories (unlimited)

### 🔧 Features

- ✅ Database-backed persistence
- ✅ 2-month event tracking (Sep 21 - Nov 21, 2025)
- ✅ Smart prize selection with fallback
- ✅ Real-time inventory management
- ✅ Admin controls and analytics
- ✅ Mobile-responsive design
- ✅ CSV-driven prize configuration
- ✅ Daily limits for rare and ultra-rare prizes
- ✅ Server-authoritative wheel positioning

### 🎯 User Experience

- All 22 prizes always visible on wheel
- Even wheel slices (16.36° each)
- No availability messages shown to users
- Backend handles all complexity silently
- Always awards something - never disappoints

**Ready to spin and win!** 🎱

### 🔧 Recent Fixes (September 22, 2025)

- ✅ **Daily Limit Enforcement**: Fixed issue with rare and ultra-rare items exceeding daily limits
- ✅ **Prize Selection Algorithm**: Improved algorithm to ensure fair distribution
- ✅ **CSV Format**: Simplified CSV format for easier management
- ✅ **Error Handling**: Added robust error handling for edge cases
- ✅ **Admin Testing**: Enhanced admin tools for testing prize selection
- ✅ **Documentation**: Updated documentation with latest changes

### ⚠️ Pending Critical Fix

There is a critical issue with the wheel positioning logic that needs to be addressed:

```python
# CURRENT (broken):
sector_index = (selected_prize['id'] - 1) % 23  # ← HARDCODED 23!
sector_center = (sector_index * (360 / 23))     # ← HARDCODED 23!

# NEEDED FIX:
total_prizes = len(get_all_active_prizes())
sector_index = (selected_prize['id'] - 1) % total_prizes  
sector_center = (sector_index * (360 / total_prizes))
```

This fix is critical to ensure the wheel lands on the correct prize when the number of prizes changes.
