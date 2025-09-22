@echo off
echo === STOPPING PICKERWHEEL DOCKER CONTAINER ===
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

echo Stopping Docker container...
docker-compose down

if %errorlevel% equ 0 (
    echo ✅ PickerWheel Docker container stopped successfully!
) else (
    echo ❌ Failed to stop PickerWheel Docker container
    echo Please check the error messages above.
)

pause
