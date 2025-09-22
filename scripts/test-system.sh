#!/bin/bash

# Test PickerWheel v4 Clean System

echo "🧪 Testing PickerWheel v4 Clean System..."

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Please run this from the pickerwheel-v4-clean directory"
    exit 1
fi

echo "📁 Checking project structure..."

# Check backend files
if [ -f "backend/backend-api.py" ]; then
    echo "✅ Backend API found"
else
    echo "❌ Backend API missing"
fi

if [ -f "backend/database-schema.sql" ]; then
    echo "✅ Database schema found"
else
    echo "❌ Database schema missing"
fi

# Check frontend files
if [ -f "frontend/index.html" ]; then
    echo "✅ Frontend index found"
else
    echo "❌ Frontend index missing"
fi

if [ -f "frontend/app.js" ]; then
    echo "✅ Frontend app found"
else
    echo "❌ Frontend app missing"
fi

if [ -f "frontend/admin.html" ]; then
    echo "✅ Admin panel found"
else
    echo "❌ Admin panel missing"
fi

# Check assets
if [ -f "assets/images/myt-mobiles-logo.png" ]; then
    echo "✅ Logo found"
else
    echo "❌ Logo missing"
fi

# Check scripts
if [ -f "scripts/start-server.sh" ]; then
    echo "✅ Start script found"
else
    echo "❌ Start script missing"
fi

echo ""
echo "🔍 System structure check complete!"
echo ""
echo "🚀 To start the system:"
echo "   ./scripts/start-server.sh"
echo ""
echo "🌐 Access points:"
echo "   • Main Contest: http://localhost:9080"
echo "   • Admin Panel: http://localhost:9080/admin.html"
echo "   • API Health: http://localhost:9080/api/health"
