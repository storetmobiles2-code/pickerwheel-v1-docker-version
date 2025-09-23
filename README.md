# 🎡 PickerWheel Contest Application

A professional spin wheel contest application with daily prize management, real-time inventory tracking, and comprehensive admin controls.

---

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose installed
- Port 8082 available

### **Start the Application**

#### **macOS/Linux:**
```bash
./scripts/docker.sh start
```

#### **Windows:**
```batch
docker-manager.bat start
```

### **Access the Application**
- **Main Contest:** http://localhost:8082
- **Admin Panel:** http://localhost:8082/admin.html
- **Admin Password:** `myTAdmin2025`

### **Stop the Application**

#### **macOS/Linux:**
```bash
./scripts/docker.sh stop
```

#### **Windows:**
```batch
docker-manager.bat stop
```

---

## 📋 **Available Commands**

### **Docker Management (macOS/Linux)**
```bash
./scripts/docker.sh start     # Start the application
./scripts/docker.sh stop      # Stop the application  
./scripts/docker.sh restart   # Restart the application
./scripts/docker.sh status    # Check container status
./scripts/docker.sh logs      # View application logs
./scripts/docker.sh info      # Show system information
```

### **Docker Management (Windows)**
```batch
docker-manager.bat start      # Start the application
docker-manager.bat stop       # Stop the application
docker-manager.bat restart    # Restart the application
docker-manager.bat status     # Check container status
docker-manager.bat logs       # View application logs
```

---

## 🏗️ **System Architecture**

### **Components**
- **Frontend:** HTML5, CSS3, JavaScript (Vanilla)
- **Backend:** Python Flask with SQLite database
- **Containerization:** Docker with multi-platform support
- **Prize Management:** Daily CSV-based configuration system

### **Key Features**
- 🎡 **Interactive Spin Wheel** with precise alignment
- 🏆 **Daily Prize Management** with automatic date transitions
- 📊 **Real-time Inventory Tracking** with daily limits
- 🎨 **Custom Icons & Combo Emojis** for visual appeal
- 🔊 **Sound Effects & Celebrations** with confetti animations
- 📋 **Daily Prizes Log** with audit trail
- 🛠️ **Comprehensive Admin Panel** with live controls
- 🔄 **Aggressive Rare Item Selection** for guaranteed wins

### **Database Schema**
- **daily_prizes:** Prize definitions with categories and limits
- **daily_inventory:** Real-time quantity tracking
- **daily_transactions:** Complete audit log of all activities

---

## 🎮 **How It Works**

### **Prize Categories**
- **Common Items (6 items):** 30 quantity, 5 daily limit each
- **Rare Items (9 items):** Variable quantity, 1 daily limit each  
- **Ultra-Rare Items (6 items):** Limited quantity, 1 daily limit each

### **Selection Logic**
- **Aggressive Boosting:** Rare/ultra-rare items get priority selection
- **Daily Limits:** Items become unavailable after reaching daily limit
- **Inventory Tracking:** Real-time quantity decrements on wins
- **Date Transitions:** Automatic reset at midnight (IST timezone)

### **Visual System**
- **Single Items:** Custom PNG icons (gas-stove.png, smart-tv.png, etc.)
- **Combo Items:** Emoji combinations (⌚+❄️, 🔋+🎧, 🎧+🔊)
- **Fallback System:** Graceful degradation to emojis if icons fail

---

## 🛠️ **Configuration**

### **Prize Configuration**
Edit `itemlist_dates_v2.txt` to modify prizes:
```csv
ID,Item Name,Category,Quantity,Daily Limit,Available Dates,Emoji,Description
1,smartwatch + mini cooler,common,30,5,*,⌚,Smartwatch with mini cooler combo
```

### **Daily CSV Generation**
```bash
python scripts/update_csvs_from_v2.py
```

### **Environment Variables**
- **TZ:** Asia/Kolkata (IST timezone)
- **PORT:** 8082 (configurable in docker-compose.yml)

---

## 🔧 **Admin Panel Features**

### **System Management**
- **Database Status:** View current inventory and limits
- **Daily CSV Loading:** Import prize data for specific dates
- **Live Inventory Control:** Adjust quantities in real-time
- **System Reset:** Clear transactions and reload data

### **Testing & Validation**
- **Aggressive Selection Testing:** Verify rare item priority
- **Daily Limits Status:** Monitor limit enforcement
- **Audit Log:** Complete transaction history with filtering

### **Data Export/Import**
- **Export to CSV:** Backup current database state
- **Reload from Master:** Reset from itemlist_dates_v2.txt
- **Sync All Dates:** Load all future dates into database

---

## 🐛 **Debugging Guide**

### **Common Issues**

#### **Wheel Alignment Problems**
- Check browser console for segment mapping logs
- Verify prize IDs match between database and frontend
- Ensure `itemlist_dates_v2.txt` format is correct

#### **Prize Selection Issues**
- Check daily limits in admin panel
- Verify inventory quantities are > 0
- Review aggressive selection logs in backend

#### **Database Issues**
- Use admin panel "Database Status" to check integrity
- Reset database via admin panel if corrupted
- Check timezone settings (should be IST)

### **Debug Endpoints**
- **GET /api/prizes/wheel-display:** View all wheel prizes
- **GET /api/admin/daily-limits-status:** Check daily limits
- **GET /api/admin/database-status:** Database health check
- **GET /api/audit-log:** Complete transaction history

### **Log Analysis**
```bash
./scripts/docker.sh logs | grep -E "(ERROR|WARNING|🎯|🏆)"
```

---

## 🔄 **Development Workflow**

### **Making Changes**
1. Edit source files (frontend/, backend/, itemlist_dates_v2.txt)
2. Restart container: `./scripts/docker.sh restart`
3. Test changes via admin panel
4. Check logs for any errors

### **Adding New Prizes**
1. Add to `itemlist_dates_v2.txt` with proper format
2. Add icon to `frontend/icons/` (optional)
3. Update icon mapping in `frontend/wheel.js` (if needed)
4. Regenerate CSVs: `python scripts/update_csvs_from_v2.py`
5. Restart application

### **Backup & Restore**
```bash
# Backup database
cp backend/pickerwheel_contest.db backup_$(date +%Y%m%d).db

# Restore database  
cp backup_20250923.db backend/pickerwheel_contest.db
./scripts/docker.sh restart
```

---

## 🌐 **Cross-Platform Support**

### **macOS/Linux**
- Use `./scripts/docker.sh` for all operations
- Supports all Docker features and commands
- Full logging and system information

### **Windows**
- Use `docker-manager.bat` for basic operations
- Simplified interface with essential commands
- Compatible with Windows Command Prompt and PowerShell

### **Network Access**
The application is accessible from other devices on the same network:
- Find your IP: `./scripts/docker.sh info` (macOS/Linux)
- Access via: `http://YOUR_IP:8082`

---

## 📊 **System Requirements**

### **Minimum Requirements**
- **RAM:** 512MB available
- **Storage:** 100MB free space
- **Network:** Port 8082 available
- **Docker:** Version 20.0+ recommended

### **Recommended Requirements**
- **RAM:** 1GB available for smooth operation
- **Storage:** 500MB for logs and backups
- **Network:** Stable connection for multi-device access

---

## 🆘 **Support & Troubleshooting**

### **Quick Fixes**
1. **Container won't start:** Check if port 8082 is in use
2. **Database errors:** Use admin panel to reset database
3. **Wheel not spinning:** Clear browser cache and reload
4. **Icons not loading:** Check `frontend/icons/` directory exists

### **Reset Everything**
```bash
./scripts/docker.sh stop
docker system prune -f
./scripts/docker.sh start
```

### **Get System Information**
```bash
./scripts/docker.sh info    # macOS/Linux
docker-manager.bat status   # Windows
```

---

## 📝 **License & Credits**

**PickerWheel Contest Application**  
Built with modern web technologies and Docker for cross-platform compatibility.

**Key Technologies:**
- Frontend: Vanilla JavaScript, CSS3, HTML5
- Backend: Python Flask, SQLite
- Containerization: Docker, Docker Compose
- Icons: Custom PNG assets with emoji fallbacks

---

*For technical support or feature requests, check the admin panel logs and system status first.*