@echo off
echo === IMPORTING AND STARTING PICKERWHEEL DOCKER CONTAINER ===
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not running
    echo Please start Docker Desktop and try again
    exit /b 1
)

REM Check if pickerwheel.tar exists
if exist pickerwheel.tar (
    echo Found Docker image file: pickerwheel.tar
    echo Importing Docker image...
    
    call import-docker-image.bat
    
    if %errorlevel% neq 0 (
        echo Failed to import Docker image
        echo Please check the error messages above.
        exit /b 1
    )
) else (
    echo Docker image file not found. Will build from source.
)

echo Starting Docker container...
call start-docker.bat

if %errorlevel% neq 0 (
    echo Failed to start Docker container
    echo Please check the error messages above.
    exit /b 1
)

echo PickerWheel Docker container imported and started successfully!
pause
