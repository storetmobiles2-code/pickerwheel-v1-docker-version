@echo off
setlocal enabledelayedexpansion
color 0E
cls

echo ================================================
echo      Stopping PickerWheel v2 Containers
echo ================================================
echo.

REM Check if Docker is running
docker info > nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    echo.
    pause
    exit /b 1
)

REM Change to script directory then parent
cd /d "%~dp0"
cd ..

echo Stopping all PickerWheel containers...
echo.

REM Check for docker compose v2 or docker-compose v1
docker compose version > nul 2>&1
if errorlevel 1 (
    docker-compose -f docker-compose.yml down
) else (
    docker compose -f docker-compose.yml down
)

if errorlevel 1 (
    color 0C
    echo WARNING: Some containers may not have stopped properly.
    echo Trying force stop...
    docker stop pickerwheel-app pickerwheel-db pickerwheel-redis 2>nul
)

color 0A
echo.
echo ================================================
echo      PickerWheel containers stopped!
echo ================================================
echo.
echo NOTE: Database data is preserved in Docker volumes.
echo       Use docker-menu.bat "Clean" to remove all data.
echo.
pause
