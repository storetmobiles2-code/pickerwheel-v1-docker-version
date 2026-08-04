@echo off
setlocal enabledelayedexpansion
color 0A
cls

echo ================================================
echo    Starting PickerWheel v2 (PostgreSQL)
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

echo Step 1: Building and starting containers...
echo.

REM Check for docker compose v2 or docker-compose v1
docker compose version > nul 2>&1
if errorlevel 1 (
    docker-compose -f docker-compose.yml up -d --build
) else (
    docker compose -f docker-compose.yml up -d --build
)

if errorlevel 1 (
    color 0C
    echo ERROR: Failed to start containers!
    echo Check Docker logs for more details.
    pause
    exit /b 1
)

echo.
echo Step 2: Waiting for PostgreSQL to be ready...
timeout /t 8 /nobreak > nul

REM Check PostgreSQL health
echo Checking database connection...
docker exec pickerwheel-db pg_isready -U pickerwheel -d pickerwheel > nul 2>&1
if errorlevel 1 (
    echo Waiting for PostgreSQL...
    timeout /t 5 /nobreak > nul
)

echo.
echo Step 3: Opening PickerWheel in your browser...
start http://localhost:9080

cls
color 0A
echo ================================================
echo      PickerWheel v2 is now running!
echo ================================================
echo.
echo Access URLs:
echo   - Main Wheel:    http://localhost:9080
echo   - Admin Panel:   http://localhost:9080/admin
echo.
echo Network Access (for other devices):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo   - Main Wheel:    http://!ip!:9080
    echo   - Admin Panel:   http://!ip!:9080/admin
    goto :break
)
:break
echo.
echo Admin Password: myTAdmin2025
echo.
echo ================================================
echo Commands:
echo   - Stop:      stop-pickerwheel.bat
echo   - Restart:   restart-pickerwheel.bat
echo   - Menu:      docker-menu.bat
echo ================================================
echo.
echo NOTE: If this is the first run, you may need to
echo       run the data migration from the menu.
echo.
pause
