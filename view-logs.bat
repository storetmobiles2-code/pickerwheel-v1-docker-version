@echo off
echo === PICKERWHEEL DOCKER CONTAINER LOGS ===
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

echo Showing logs (press Ctrl+C to exit)...
echo.
docker-compose logs -f

pause
