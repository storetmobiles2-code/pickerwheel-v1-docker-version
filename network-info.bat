@echo off
echo === PICKERWHEEL NETWORK INFORMATION ===
echo.

echo Your IP Addresses:
ipconfig | findstr /r /c:"IPv4 Address"
echo.

echo Testing if port 8080 is accessible...
netstat -an | findstr :8080
echo.

echo Docker container status:
docker-compose ps
echo.

echo If your mobile device cannot connect, try these troubleshooting steps:
echo 1. Make sure your mobile device is on the same WiFi network
echo 2. Check if your computer's firewall is blocking incoming connections
echo 3. Try accessing http://YOUR_IP_ADDRESS:8080 directly on your mobile browser
echo 4. Restart your router if network issues persist
echo.

pause
