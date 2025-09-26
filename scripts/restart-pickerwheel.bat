@echo off
color 0E
cls

echo =======================================
echo    Restarting PickerWheel Contest...
echo =======================================
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

echo Step 1: Stopping current container...
docker-compose down
timeout /t 2 /nobreak > nul

echo.
echo Step 2: Starting fresh container...
docker-compose up -d

REM Wait for the container to be ready
echo.
echo Step 3: Waiting for system to be ready...
timeout /t 5 /nobreak > nul

REM Try to open the website
echo.
echo Step 4: Opening PickerWheel in your browser...
start http://localhost:8082

cls
color 0A
echo =======================================
echo    PickerWheel has been restarted!
echo =======================================
echo.
echo Access URLs:
echo - Main Contest: http://localhost:8082
echo - Admin Panel:  http://localhost:8082/admin.html
echo.
echo Admin Password: myTAdmin2025
echo =======================================
echo.
pause
