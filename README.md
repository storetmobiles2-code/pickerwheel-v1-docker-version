# PickerWheel Contest System v4

## Overview
Server-authoritative spin-to-win contest system with dynamic prize availability.

## Documentation
All documentation has been organized in the `docs` directory:

- [Main Documentation](docs/README.md) - Complete system overview
- [Business Rules](docs/BUSINESS_RULES.md) - Contest rules and prize distribution logic
- [Changelog](docs/CHANGELOG.md) - Version history and updates
- [Cleanup Summary](docs/CLEANUP_SUMMARY.md) - System optimization details
- [Docker Deployment](docs/DOCKER_DEPLOYMENT.md) - Detailed Docker deployment instructions

## Directory Structure
- `backend/` - Flask backend with SQLite database
- `frontend/` - HTML/CSS/JS frontend with responsive design
- `scripts/` - Utility scripts for server management
  - `start-docker.sh` - Start Docker container
  - `stop-docker.sh` - Stop Docker container
- `templates/` - Configuration templates
- `docs/` - Complete documentation
- `Dockerfile` - Docker container definition
- `docker-compose.yml` - Docker Compose configuration

## Quick Start (Local)
1. Start the server: `./scripts/start-server.sh`
2. Access the application: `http://localhost:9080`
3. Admin access: Use Ctrl+Alt+A and password "myTAdmin2025"

**Note**: When using Docker, the application is accessible on port 8080 instead of 9080.

## Docker Deployment

### macOS / Linux

#### Quick Start (Recommended)
1. Install [Docker](https://www.docker.com/products/docker-desktop) and [Docker Compose](https://docs.docker.com/compose/install/)
2. Run the all-in-one script: `./scripts/import-and-start.sh`
   - This script will import the Docker image if available, or build it if not
   - Then it will start the Docker container
3. Access the application: `http://<your-ip-address>:8080`

#### Method 1: Using the Docker Image File
1. Install [Docker](https://www.docker.com/products/docker-desktop) and [Docker Compose](https://docs.docker.com/compose/install/)
2. Import the Docker image: `./scripts/import-docker-image.sh`
3. Start the Docker container: `./scripts/start-docker.sh`
4. Access the application: `http://<your-ip-address>:8080`
5. Stop the Docker container: `./scripts/stop-docker.sh`

#### Method 2: Building from Source
1. Install [Docker](https://www.docker.com/products/docker-desktop) and [Docker Compose](https://docs.docker.com/compose/install/)
2. Start the Docker container: `./scripts/start-docker.sh`
3. Access the application: `http://<your-ip-address>:8080`
4. Stop the Docker container: `./scripts/stop-docker.sh`

#### Exporting the Docker Image
1. Export the Docker image: `./scripts/export-docker-image.sh`
2. The image will be saved as `pickerwheel.tar` in the current directory

### Windows

#### Quick Start (Recommended)
1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Double-click on `start.bat` in the root directory
   - This script will build the Docker image and start the container
3. Access the application: `http://localhost:8080`

#### Import and Run (If you have the Docker image file)
1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
2. Make sure `pickerwheel.tar` is in the root directory
3. Double-click on `import-and-run.bat` in the root directory
4. Access the application: `http://localhost:8080`

#### Other Windows Scripts
- `stop.bat` - Stop the Docker container
- `show-network.bat` - Display network information for accessing from other devices

For detailed instructions, see [Windows README](WINDOWS_README.md)

## System Features
- Server-authoritative prize selection
- Dynamic prize availability based on CSV configuration
- Daily and total prize limits
- Admin dashboard with real-time statistics
- Database management interface
- System verification tools
