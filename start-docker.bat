@echo off
echo === STARTING PICKERWHEEL DOCKER CONTAINER ===
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

echo Building and starting Docker container...
docker-compose up -d

if %errorlevel% equ 0 (
    echo ✅ PickerWheel Docker container started successfully!
    echo.
    echo === ACCESS INFORMATION ===
    echo.
    echo Local Access:
    echo Main Contest:    http://localhost:8080
    echo Admin Panel:     http://localhost:8080/admin.html
    echo.
    echo To access from other devices on the network:
    for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /r /c:"IPv4 Address"') do (
        set IP=%%a
        set IP=!IP:~1!
        echo Main Contest:    http://!IP!:8080
        echo Admin Panel:     http://!IP!:8080/admin.html
        goto :continue
    )
    :continue
    echo.
    echo Note: If you have a firewall enabled, make sure port 8080 is allowed.
    echo.
    echo Admin Credentials:
    echo Password: myTAdmin2025 (Use Ctrl+Alt+A to access admin panel)
    echo.
    echo Commands:
    echo Stop container:   docker-compose down
    echo View logs:        docker-compose logs -f
)

pause
