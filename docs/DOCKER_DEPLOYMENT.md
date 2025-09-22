# Docker Deployment Guide

## Overview
This guide provides detailed instructions for deploying the PickerWheel Contest application using Docker. Docker allows you to run the application in a containerized environment, making it accessible to other users on the same network.

## Prerequisites
- [Docker](https://www.docker.com/products/docker-desktop) installed on your machine
- [Docker Compose](https://docs.docker.com/compose/install/) installed on your machine
- Basic knowledge of terminal/command line

## Quick Deployment

### Using the Provided Scripts
We've included convenience scripts to make deployment easy:

1. **Start the Docker container:**
   ```bash
   ./scripts/start-docker.sh
   ```
   This script will:
   - Build the Docker image if it doesn't exist
   - Start the container
   - Display the URL to access the application

2. **Stop the Docker container:**
   ```bash
   ./scripts/stop-docker.sh
   ```
   This script will stop and remove the running container.

### Manual Deployment
If you prefer to run the commands manually:

1. **Build and start the container:**
   ```bash
   docker-compose up -d --build
   ```

2. **Stop the container:**
   ```bash
   docker-compose down
   ```

## Accessing the Application
Once the container is running, the application will be accessible at:
```
http://<your-ip-address>:9080
```

Where `<your-ip-address>` is your machine's IP address on the local network. You can find this by:
- On macOS/Linux: Run `hostname -I` or `ifconfig`
- On Windows: Run `ipconfig`

## Network Configuration
The Docker container is configured to use the host network, which means it will be accessible to other machines on the same network. If you're having trouble accessing the application from other machines, check:

1. **Firewall settings:** Make sure port 9080 is allowed in your firewall
2. **Network settings:** Ensure your network allows communication between machines

## Persistent Data
The Docker setup is configured to persist data in the following ways:

- **Database:** The SQLite database is stored in the `backend/` directory, which is mounted as a volume
- **Frontend files:** The `frontend/` directory is mounted as a volume
- **Assets:** The `assets/` directory is mounted as a volume

This means that any changes made to the application data will persist even if the container is stopped and restarted.

## Troubleshooting

### Container Won't Start
If the container fails to start, check:
1. Docker service is running
2. Port 9080 is not already in use
3. You have sufficient permissions to run Docker

Run `docker-compose logs` to see detailed error messages.

### Can't Access from Other Machines
If other machines can't access the application:
1. Verify the host machine's IP address
2. Check that port 9080 is not blocked by a firewall
3. Ensure all machines are on the same network
4. Try accessing with the full URL: `http://<your-ip-address>:9080`

### Database Issues
If you encounter database issues:
1. Check that the database file exists in the `backend/` directory
2. Ensure the Docker user has permission to access the database file
3. Try rebuilding the container: `docker-compose up -d --build --force-recreate`

## Advanced Configuration

### Changing the Port
If you need to change the port (e.g., if 9080 is already in use), edit the `docker-compose.yml` file:
```yaml
ports:
  - "new_port:9080"
```
Replace `new_port` with your desired port number.

### Production Deployment
For production deployment, consider:
1. Setting `debug=False` in `backend/backend-api.py`
2. Using a reverse proxy like Nginx for SSL termination
3. Implementing proper authentication and security measures
4. Setting up monitoring and logging

## Security Considerations
- The default setup uses `debug=True`, which is not recommended for production
- The admin password is hardcoded; consider changing it for production
- The application does not use HTTPS by default; consider adding SSL for production
