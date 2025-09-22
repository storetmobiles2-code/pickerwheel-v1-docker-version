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

2. **Start the Container**
   - Double-click on `start.bat` in the root directory
   - This script will build the Docker image and start the container

3. **Access the Application**
   - Main Contest: [http://localhost:8080](http://localhost:8080)
   - Admin Panel: [http://localhost:8080/admin.html](http://localhost:8080/admin.html)
   - Admin Password: `myTAdmin2025` (Use Ctrl+Alt+A to access)

4. **Stop the Container When Done**
   - Double-click on `stop.bat` in the root directory

### Import and Run (If you have the Docker image file)

1. **Start Docker Desktop**
   - Make sure Docker Desktop is running before proceeding

2. **Import and Start in One Step**
   - Make sure `pickerwheel.tar` is in the root directory
   - Double-click on `import-and-run.bat` in the root directory
   - This will import the Docker image and start the container

3. **Access the Application**
   - Main Contest: [http://localhost:8080](http://localhost:8080)
   - Admin Panel: [http://localhost:8080/admin.html](http://localhost:8080/admin.html)
   - Admin Password: `myTAdmin2025` (Use Ctrl+Alt+A to access)

4. **Stop the Container**
   - Double-click on `stop.bat` in the root directory

## Available Scripts

### Root Directory Scripts

- `start.bat` - Build and start the Docker container
- `stop.bat` - Stop the Docker container
- `import-and-run.bat` - Import the Docker image and start the container
- `show-network.bat` - Display network information for accessing from other devices

### Scripts Directory

All scripts are also available in the `scripts` directory with more advanced options:

- `scripts/start-docker.bat` - Build and start the Docker container
- `scripts/stop-docker.bat` - Stop the Docker container
- `scripts/import-docker-image.bat` - Import the Docker image
- `scripts/import-and-start.bat` - Import the Docker image and start the container
- `scripts/show-ip-info.bat` - Display detailed network information
- `scripts/network-info.bat` - Display basic network information
- `scripts/view-logs.bat` - View Docker container logs

## Network Access

To access the application from other devices on your network (like mobile phones or tablets):

1. **Find Your IP Address**
   - Double-click on `show-network.bat` in the root directory
   - This will display all your IP addresses and formatted URLs
   - Use the displayed URLs on your mobile device

2. **Alternative Method**
   - Navigate to the `scripts` directory
   - Double-click on `network-info.bat` or `show-ip-info.bat`
   - These will show network information and test if port 8080 is accessible

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
