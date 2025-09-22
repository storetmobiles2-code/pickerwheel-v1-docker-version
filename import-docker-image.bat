@echo off
echo === IMPORTING PICKERWHEEL DOCKER IMAGE ===
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

REM Check if pickerwheel.tar exists
if not exist pickerwheel.tar (
    echo Error: pickerwheel.tar not found
    echo Please make sure the file is in the current directory
    echo Current directory: %CD%
    exit /b 1
)

echo Importing Docker image from pickerwheel.tar...
docker load -i pickerwheel.tar

if %errorlevel% equ 0 (
    echo ✅ Docker image imported successfully!
    echo.
    echo You can now start the container using start-docker.bat
) else (
    echo ❌ Failed to import Docker image
    echo Please check the error messages above.
)

pause
