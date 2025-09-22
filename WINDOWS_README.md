# PickerWheel Docker - Windows Instructions

## Prerequisites

1. **Install Docker Desktop for Windows**
   - Download from [Docker's official website](https://www.docker.com/products/docker-desktop)
   - Follow the installation instructions
   - Make sure to enable WSL 2 (Windows Subsystem for Linux) if prompted

2. **Enable Virtualization**
   - Make sure virtualization is enabled in your BIOS/UEFI settings
   - This is required for Docker to work properly on Windows

## Quick Start

### One-Click Setup (Recommended)

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running before proceeding

2. **Import and Start in One Step**
   - Double-click on `import-and-start.bat`
   - This script will:
     - Import the Docker image if `pickerwheel.tar` exists
     - Or build the image from source if the file doesn't exist
     - Start the Docker container automatically

3. **Access the Application**
   - Main Contest: [http://localhost:8080](http://localhost:8080)
   - Admin Panel: [http://localhost:8080/admin.html](http://localhost:8080/admin.html)
   - Admin Password: `myTAdmin2025` (Use Ctrl+Alt+A to access)

4. **Stop the Container When Done**
   - Double-click on `stop-docker.bat`

### Method 1: Using the Docker Image File

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running before proceeding

2. **Import the Docker Image**
   - Make sure `pickerwheel.tar` is in the same directory as the scripts
   - Double-click on `import-docker-image.bat`
   - Wait for the import to complete

3. **Start the PickerWheel Container**
   - Double-click on `start-docker.bat`

4. **Access the Application**
   - Main Contest: [http://localhost:8080](http://localhost:8080)
   - Admin Panel: [http://localhost:8080/admin.html](http://localhost:8080/admin.html)
   - Admin Password: `myTAdmin2025` (Use Ctrl+Alt+A to access)

5. **Stop the Container**
   - Double-click on `stop-docker.bat`

### Method 2: Building from Source

1. **Start Docker Desktop**

2. **Start the PickerWheel Container**
   - Double-click on `start-docker.bat`
   - This will build the Docker image and start the container

3. **Access the Application**
   - Same as Method 1

## Troubleshooting

### Docker Not Running
If you see "Docker is not running" error:
- Make sure Docker Desktop is running
- Check the Docker icon in the system tray
- Restart Docker Desktop if necessary

### Port Conflict
If port 8080 is already in use:
1. Edit `docker-compose.yml`
2. Change the port mapping from `"8080:9080"` to another port like `"8081:9080"`
3. Restart the container

### Firewall Issues
If you can't access the application from other devices:
1. Open Windows Defender Firewall
2. Allow incoming connections on port 8080
3. Allow Docker Desktop through the firewall

### Performance Issues
If the application is running slowly:
1. Open Docker Desktop settings
2. Increase the resources allocated to Docker (CPU, Memory)
3. Restart Docker Desktop

## Commands

- **Start Container**: `start-docker.bat`
- **Stop Container**: `stop-docker.bat`
- **View Logs**: `view-logs.bat`

## Network Access

To access the application from other devices on the same network:
1. Find your computer's IP address (shown when starting the container)
2. On other devices, open a browser and go to:
   - `http://YOUR_IP_ADDRESS:8080`

## Data Persistence

The application data is stored in the Docker container. If you remove the container, the data will be lost.

To backup the data:
1. Stop the container
2. Copy the entire project directory to a safe location
3. Restart the container
