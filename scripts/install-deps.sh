#!/bin/bash

# Install Python Dependencies for PickerWheel v4

echo "📦 Installing Python dependencies for PickerWheel v4..."

cd backend

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "📋 Required packages:"
cat requirements.txt

echo ""
echo "🔧 Installing dependencies..."

# Try different installation methods
if pip3 install -r requirements.txt --break-system-packages --user 2>/dev/null; then
    echo "✅ Dependencies installed successfully with pip3!"
elif python3 -m pip install -r requirements.txt --break-system-packages --user 2>/dev/null; then
    echo "✅ Dependencies installed successfully with python3 -m pip!"
elif pip3 install -r requirements.txt --user 2>/dev/null; then
    echo "✅ Dependencies installed successfully with --user flag!"
else
    echo "⚠️ Standard installation failed, trying alternative methods..."
    
    # Try installing each package individually
    while IFS= read -r package; do
        if [ ! -z "$package" ] && [[ ! "$package" =~ ^#.* ]]; then
            echo "📦 Installing $package..."
            pip3 install "$package" --break-system-packages --user 2>/dev/null || \
            python3 -m pip install "$package" --break-system-packages --user 2>/dev/null || \
            echo "⚠️ Failed to install $package"
        fi
    done < requirements.txt
fi

echo ""
echo "🧪 Testing imports..."

# Test if Flask can be imported
python3 -c "
try:
    import flask
    print('✅ Flask imported successfully')
    print(f'   Version: {flask.__version__}')
except ImportError as e:
    print('❌ Flask import failed:', e)
    exit(1)

try:
    import flask_cors
    print('✅ Flask-CORS imported successfully')
except ImportError as e:
    print('❌ Flask-CORS import failed:', e)
    exit(1)

try:
    import werkzeug
    print('✅ Werkzeug imported successfully')
    print(f'   Version: {werkzeug.__version__}')
except ImportError as e:
    print('❌ Werkzeug import failed:', e)
    exit(1)

print('🎉 All dependencies are working!')
" || {
    echo "❌ Dependency test failed!"
    echo ""
    echo "💡 Manual installation options:"
    echo "   1. Use virtual environment:"
    echo "      python3 -m venv venv"
    echo "      source venv/bin/activate"
    echo "      pip install -r requirements.txt"
    echo ""
    echo "   2. Use pipx (if available):"
    echo "      brew install pipx"
    echo "      pipx install flask flask-cors werkzeug"
    echo ""
    echo "   3. Use conda (if available):"
    echo "      conda install flask flask-cors werkzeug"
    exit 1
}

echo ""
echo "✅ Dependency installation complete!"
echo "🚀 Ready to start server with: ../scripts/start-server.sh"
