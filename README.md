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

#### **Windows (Simple Method):**
1. Make sure Docker Desktop is running
2. Double-click `scripts/start-pickerwheel.bat`
3. The application will start and open in your browser automatically

### **Access the Application**
- **Main Contest:** http://localhost:8082
- **Admin Panel:** http://localhost:8082/admin.html
- **Admin Password:** `myTAdmin2025`

### **Stop the Application**

#### **macOS/Linux:**
```bash
./scripts/docker.sh stop
```

#### **Windows (Simple Method):**
1. Double-click `scripts/stop-pickerwheel.bat`
2. Wait for confirmation that the system has stopped

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
./scripts/docker.sh test      # Run system tests
./scripts/docker.sh clean     # Clean Docker resources
```

### **Docker Management (Windows)**
#### Simple Method (Recommended for Non-Technical Users)
- `scripts/start-pickerwheel.bat` - Start the application and open in browser
- `scripts/stop-pickerwheel.bat` - Stop the application

#### Advanced Method (For Technical Users)
```batch
docker-manager.bat start      # Start the application
docker-manager.bat stop       # Stop the application
docker-manager.bat restart    # Restart the application
docker-manager.bat status     # Check container status
docker-manager.bat logs       # View application logs
```

[Rest of the README remains unchanged...]