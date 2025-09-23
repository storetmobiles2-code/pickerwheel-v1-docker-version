@echo off
REM PickerWheel Docker Manager for Windows
REM Simple batch file to manage Docker containers

setlocal enabledelayedexpansion

REM Colors for output
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "BLUE=[94m"
set "RESET=[0m"

REM Container and image names
set "CONTAINER_NAME=pickerwheel-v1-docker-version-pickerwheel-1"
set "COMPOSE_FILE=docker-compose.yml"

if "%1"=="" (
    goto :show_help
)

if /i "%1"=="start" goto :start_container
if /i "%1"=="stop" goto :stop_container
if /i "%1"=="restart" goto :restart_container
if /i "%1"=="status" goto :check_status
if /i "%1"=="logs" goto :show_logs
if /i "%1"=="help" goto :show_help

echo %RED%Error: Unknown command '%1'%RESET%
goto :show_help

:start_container
echo %YELLOW%=== STARTING PICKERWHEEL DOCKER CONTAINER ===%RESET%
echo.
echo %YELLOW%Building and starting container...%RESET%
docker-compose up -d --build
if %errorlevel% equ 0 (
    echo %GREEN%✅ PickerWheel Docker container started successfully!%RESET%
    echo.
    goto :show_access_info
) else (
    echo %RED%❌ Failed to start container%RESET%
    exit /b 1
)

:stop_container
echo %YELLOW%=== STOPPING PICKERWHEEL DOCKER CONTAINER ===%RESET%
echo.
echo %YELLOW%Stopping container...%RESET%
docker-compose down
if %errorlevel% equ 0 (
    echo %GREEN%✅ PickerWheel Docker container stopped successfully!%RESET%
) else (
    echo %RED%❌ Failed to stop container%RESET%
    exit /b 1
)
goto :end

:restart_container
echo %YELLOW%=== RESTARTING PICKERWHEEL DOCKER CONTAINER ===%RESET%
echo.
echo %YELLOW%Stopping existing container...%RESET%
docker-compose down
echo %YELLOW%Starting fresh container...%RESET%
docker-compose up -d --build
if %errorlevel% equ 0 (
    echo %GREEN%✅ PickerWheel Docker container restarted successfully!%RESET%
    echo.
    goto :show_access_info
) else (
    echo %RED%❌ Failed to restart container%RESET%
    exit /b 1
)

:check_status
echo %YELLOW%=== PICKERWHEEL DOCKER STATUS ===%RESET%
echo.
echo %YELLOW%Container Status:%RESET%
docker-compose ps
echo.
echo %YELLOW%Docker System Info:%RESET%
docker system df
echo.
echo %YELLOW%Network Information:%RESET%
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    set "ip=%%i"
    set "ip=!ip: =!"
    if not "!ip!"=="" (
        echo Local IP: !ip!
        echo Network Access: http://!ip!:8082
    )
)
goto :end

:show_logs
echo %YELLOW%=== PICKERWHEEL DOCKER LOGS ===%RESET%
echo.
echo %YELLOW%Recent container logs (press Ctrl+C to exit):%RESET%
docker-compose logs -f --tail=50
goto :end

:show_access_info
echo %YELLOW%=== ACCESS INFORMATION ===%RESET%
echo.
echo %GREEN%Local Access:%RESET%
echo Main Contest:    %BLUE%http://localhost:8082%RESET%
echo Admin Panel:     %BLUE%http://localhost:8082/admin.html%RESET%
echo.
echo %GREEN%Network Access (for other devices):%RESET%
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4"') do (
    set "ip=%%i"
    set "ip=!ip: =!"
    if not "!ip!"=="" (
        echo Main Contest:    %BLUE%http://!ip!:8082%RESET%
        echo Admin Panel:     %BLUE%http://!ip!:8082/admin.html%RESET%
        goto :access_info_done
    )
)
:access_info_done
echo.
echo %YELLOW%Note:%RESET% If you have a firewall enabled, make sure port 8082 is allowed.
echo.
echo %GREEN%Admin Credentials:%RESET%
echo Password: %BLUE%myTAdmin2025%RESET% (Use Ctrl+Alt+A to access admin panel)
echo.
echo %YELLOW%Commands:%RESET%
echo Stop container:   %BLUE%docker-manager.bat stop%RESET%
echo View logs:        %BLUE%docker-manager.bat logs%RESET%
echo Check status:     %BLUE%docker-manager.bat status%RESET%
echo Restart:          %BLUE%docker-manager.bat restart%RESET%
goto :end

:show_help
echo %YELLOW%=== PICKERWHEEL DOCKER MANAGER ===%RESET%
echo.
echo %GREEN%Usage:%RESET% docker-manager.bat [command]
echo.
echo %YELLOW%Available Commands:%RESET%
echo   %BLUE%start%RESET%     - Start the PickerWheel application
echo   %BLUE%stop%RESET%      - Stop the PickerWheel application
echo   %BLUE%restart%RESET%   - Restart the PickerWheel application
echo   %BLUE%status%RESET%    - Check container and system status
echo   %BLUE%logs%RESET%      - View application logs (live)
echo   %BLUE%help%RESET%      - Show this help message
echo.
echo %YELLOW%Examples:%RESET%
echo   docker-manager.bat start
echo   docker-manager.bat stop
echo   docker-manager.bat restart
echo   docker-manager.bat status
echo   docker-manager.bat logs
echo.
echo %YELLOW%Requirements:%RESET%
echo   - Docker Desktop for Windows installed and running
echo   - Port 8082 available
echo.
echo %YELLOW%Access URLs:%RESET%
echo   - Main Contest: http://localhost:8082
echo   - Admin Panel:  http://localhost:8082/admin.html
echo   - Admin Password: myTAdmin2025

:end
endlocal
