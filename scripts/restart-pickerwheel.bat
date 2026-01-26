@echo off
setlocal enabledelayedexpansion
color 0E
cls

echo ================================================
echo      Restarting PickerWheel v2 Containers
echo ================================================
echo.

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

REM Change to script directory then parent
cd /d "%~dp0"
cd ..

echo Step 1: Stopping existing containers...
echo.

REM Check for docker compose v2 or docker-compose v1
docker compose version > nul 2>&1
if errorlevel 1 (
    docker-compose -f docker-compose.yml down
) else (
    docker compose -f docker-compose.yml down
)

echo.
echo Step 2: Waiting for cleanup...
timeout /t 3 /nobreak > nul

echo.
echo Step 3: Starting fresh containers...
echo.

docker compose version > nul 2>&1
if errorlevel 1 (
    docker-compose -f docker-compose.yml up -d --build
) else (
    docker compose -f docker-compose.yml up -d --build
)

if errorlevel 1 (
    color 0C
    echo ERROR: Failed to start containers!
    pause
    exit /b 1
)

echo.
echo Step 4: Waiting for PostgreSQL to be ready...
timeout /t 8 /nobreak > nul

cls
color 0A
echo ================================================
echo      PickerWheel v2 restarted successfully!
echo ================================================
echo.
echo Access URLs:
echo   - Main Wheel:    http://localhost:9080
echo   - Admin Panel:   http://localhost:9080/admin
echo.
echo Admin Password: myTAdmin2025
echo ================================================
echo.
pause
