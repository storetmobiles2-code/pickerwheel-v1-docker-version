@echo off
setlocal enabledelayedexpansion
mode con: cols=80 lines=40
color 0B

REM Change to script directory then parent
cd /d "%~dp0"
cd ..

:menu
cls
echo ===============================================================
echo           PickerWheel v2 Docker Manager (PostgreSQL)
echo ===============================================================
echo.
echo Current Status:
docker ps --filter "name=pickerwheel" --format "table {{.Names}}\t{{.Status}}" 2>nul
echo.
echo ===============================================================
echo.
echo   MAIN COMMANDS:
echo   1) Start PickerWheel
echo   2) Stop PickerWheel
echo   3) Restart PickerWheel
echo.
echo   DATABASE:
echo   4) Run Data Migration
echo   5) Open Database Shell (PostgreSQL)
echo   6) View Database Logs
echo.
echo   DIAGNOSTICS:
echo   7) View Application Logs
echo   8) Show System Info
echo   9) Test API Endpoints
echo.
echo   MAINTENANCE:
echo   C) Clean Docker Resources (CAUTION!)
echo   B) Open in Browser
echo.
echo   L) Use Legacy Backend (SQLite)
echo   0) Exit
echo.
echo ===============================================================

set /p choice="Select an option: "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto migrate
if "%choice%"=="5" goto dbshell
if "%choice%"=="6" goto dblogs
if "%choice%"=="7" goto logs
if "%choice%"=="8" goto info
if "%choice%"=="9" goto test
if /i "%choice%"=="C" goto clean
if /i "%choice%"=="B" goto browser
if /i "%choice%"=="L" goto legacy
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
timeout /t 2 /nobreak > nul
goto menu

:start
cls
echo Starting PickerWheel...
call "%~dp0start-pickerwheel.bat"
goto menu

:stop
cls
echo Stopping PickerWheel...
call "%~dp0stop-pickerwheel.bat"
goto menu

:restart
cls
echo Restarting PickerWheel...
call "%~dp0restart-pickerwheel.bat"
goto menu

:migrate
cls
echo ===============================================================
echo              Running Data Migration
echo ===============================================================
echo.
echo This will migrate data from itemlist_dates_v2.txt to PostgreSQL.
echo.
docker exec -it pickerwheel-app python /app/backend/scripts/migrate_data.py
echo.
echo Migration complete!
pause
goto menu

:dbshell
cls
echo ===============================================================
echo              PostgreSQL Shell
echo ===============================================================
echo.
echo Type \q to exit the database shell.
echo.
docker exec -it pickerwheel-db psql -U pickerwheel -d pickerwheel
goto menu

:dblogs
cls
echo ===============================================================
echo              PostgreSQL Logs
echo ===============================================================
echo Press Ctrl+C to stop viewing logs
echo.
docker compose -f docker-compose.yml logs --tail=50 -f postgres
goto menu

:logs
cls
echo ===============================================================
echo              PickerWheel Application Logs
echo ===============================================================
echo Press Ctrl+C to stop viewing logs
echo.
docker compose -f docker-compose.yml logs --tail=50 -f pickerwheel
goto menu

:info
cls
echo ===============================================================
echo                  System Information
echo ===============================================================
echo.
echo Docker Version:
docker --version
docker compose version 2>nul
echo.
echo ---------------------------------------------------------------
echo Container Status:
docker ps --filter "name=pickerwheel" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo ---------------------------------------------------------------
echo Database Status:
docker exec pickerwheel-db pg_isready -U pickerwheel -d pickerwheel 2>nul
if not errorlevel 1 (
    echo PostgreSQL: Ready
) else (
    echo PostgreSQL: Not Ready
)
echo.
echo ---------------------------------------------------------------
echo Network Access:
echo - Local:  http://localhost:9080
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo - Network: http://!ip!:9080
    goto :info_continue
)
:info_continue
echo.
echo Admin Password: myTAdmin2025
echo.
pause
goto menu

:test
cls
echo ===============================================================
echo              Testing API Endpoints
echo ===============================================================
echo.
echo Testing Health Endpoint...
curl -s http://localhost:9080/api/health >nul 2>&1
if not errorlevel 1 (echo [OK] Health endpoint) else (echo [FAIL] Health endpoint)
echo.
echo Testing Wheel Display...
curl -s http://localhost:9080/api/prizes/wheel-display >nul 2>&1
if not errorlevel 1 (echo [OK] Wheel display) else (echo [FAIL] Wheel display)
echo.
echo Testing Available Prizes...
curl -s http://localhost:9080/api/prizes/available >nul 2>&1
if not errorlevel 1 (echo [OK] Available prizes) else (echo [FAIL] Available prizes)
echo.
echo Testing Statistics...
curl -s http://localhost:9080/api/stats >nul 2>&1
if not errorlevel 1 (echo [OK] Statistics) else (echo [FAIL] Statistics)
echo.
echo ===============================================================
pause
goto menu

:clean
cls
echo ===============================================================
echo              Cleaning Docker Resources
echo ===============================================================
echo.
echo WARNING: This will remove all containers and data!
echo.
set /p confirm="Type YES to confirm: "
if "%confirm%"=="YES" (
    docker compose -f docker-compose.yml down -v
    docker image prune -f
    echo Cleanup completed!
    pause
)
goto menu

:browser
start http://localhost:9080
goto menu

:legacy
cls
echo ===============================================================
echo              Legacy Backend (SQLite)
echo ===============================================================
echo.
echo 1) Start Legacy Backend
echo 2) Stop Legacy Backend
echo 0) Back to Main Menu
echo.
set /p lchoice="Select: "
if "%lchoice%"=="1" (
    docker compose -f docker-compose.yml up -d --build
    echo Legacy backend started on http://localhost:8082
    pause
)
if "%lchoice%"=="2" (
    docker compose -f docker-compose.yml down
    pause
)
goto menu

:end
cls
echo Thank you for using PickerWheel Docker Manager!
exit /b 0
