@echo off
setlocal enabledelayedexpansion
mode con: cols=80 lines=30
color 0B

:menu
cls
echo =======================================
echo      PickerWheel Docker Manager
echo =======================================
echo.
echo Current Status:
docker ps --filter "name=pickerwheel" --format "table {{.Status}}\t{{.Ports}}" 2>nul
echo.
echo =======================================
echo.
echo   1) Start PickerWheel
echo   2) Stop PickerWheel
echo   3) Restart PickerWheel
echo   4) View Logs
echo   5) Show System Info
echo   6) Clean Docker Resources
echo   7) Open in Browser
echo.
echo   0) Exit
echo.
echo =======================================

set /p choice="Select an option (0-7): "

if "%choice%"=="1" goto start
if "%choice%"=="2" goto stop
if "%choice%"=="3" goto restart
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto info
if "%choice%"=="6" goto clean
if "%choice%"=="7" goto browser
if "%choice%"=="0" goto end

echo Invalid option. Please try again.
timeout /t 2 /nobreak > nul
goto menu

:start
cls
echo Starting PickerWheel...
call start-pickerwheel.bat
goto menu

:stop
cls
echo Stopping PickerWheel...
call stop-pickerwheel.bat
goto menu

:restart
cls
echo Restarting PickerWheel...
call restart-pickerwheel.bat
goto menu

:logs
cls
echo =======================================
echo           PickerWheel Logs
echo =======================================
echo Press Ctrl+C to stop viewing logs
echo.
docker-compose logs --tail=50 -f
goto menu

:info
cls
echo =======================================
echo         System Information
echo =======================================
echo.
echo Docker Version:
docker --version
docker-compose --version
echo.
echo Container Status:
docker ps --filter "name=pickerwheel" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo Network Access:
echo - Local:  http://localhost:8082
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set ip=%%a
    set ip=!ip:~1!
    echo - Network: http://!ip!:8082
    goto :continue
)
:continue
echo.
echo Admin Password: myTAdmin2025
echo.
pause
goto menu

:clean
cls
echo =======================================
echo      Cleaning Docker Resources
echo =======================================
echo.
echo This will remove:
echo - Stopped containers
echo - Unused images
echo - Unused volumes
echo.
set /p confirm="Are you sure? (Y/N): "
if /i "%confirm%"=="Y" (
    docker-compose down
    docker system prune -f
    echo.
    echo Cleanup completed!
    pause
)
goto menu

:browser
start http://localhost:8082
goto menu

:end
echo.
echo Thank you for using PickerWheel Docker Manager!
echo.
