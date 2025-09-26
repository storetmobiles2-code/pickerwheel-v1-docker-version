@echo off
color 0C
cls

echo =======================================
echo    Stopping PickerWheel Contest...
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

echo Step 1: Stopping Docker container...
docker-compose down

cls
color 0A
echo =======================================
echo    PickerWheel has been stopped!
echo =======================================
echo.
echo To start PickerWheel again, use start-pickerwheel.bat
echo =======================================
echo.
pause
