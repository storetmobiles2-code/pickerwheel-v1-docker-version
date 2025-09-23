#!/bin/bash

# 🧪 PICKERWHEEL COMPREHENSIVE VALIDATION SUITE
# =============================================
# This script runs the complete validation suite and generates reports

echo "🧪 PickerWheel Comprehensive Validation Suite"
echo "============================================="
echo ""

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if PickerWheel container is running
if ! docker ps | grep -q "pickerwheel"; then
    echo "⚠️ PickerWheel container not found. Starting container..."
    cd "$(dirname "$0")/.."
    ./scripts/docker.sh start
    
    # Wait for container to be ready
    echo "⏳ Waiting for container to be ready..."
    sleep 10
    
    # Test if API is responding
    for i in {1..30}; do
        if curl -s http://localhost:8082/api/admin/database-status?admin_password=myTAdmin2025 > /dev/null; then
            echo "✅ Container is ready!"
            break
        fi
        echo "⏳ Waiting... ($i/30)"
        sleep 2
    done
fi

# Verify API is accessible
echo "🔍 Verifying API accessibility..."
if ! curl -s http://localhost:8082/api/admin/database-status?admin_password=myTAdmin2025 > /dev/null; then
    echo "❌ API is not accessible. Please check the container status."
    exit 1
fi

echo "✅ API is accessible. Starting validation suite..."
echo ""

# Change to scripts directory
cd "$(dirname "$0")"

# Install required Python packages if not available
echo "📦 Checking Python dependencies..."
python3 -c "import requests" 2>/dev/null || {
    echo "⚠️ Installing requests module..."
    pip3 install requests
}

# Run the comprehensive validation suite
echo "🚀 Running comprehensive validation tests..."
echo "This may take 10-15 minutes to complete all tests..."
echo ""

# Create timestamp for this run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="validation_results_$TIMESTAMP"
mkdir -p "$RESULTS_DIR"

# Run validation suite
echo "📊 Executing validation suite..."
python3 comprehensive_validation.py 2>&1 | tee "$RESULTS_DIR/validation_log.txt"

# Check if validation completed successfully
if [ -f "validation_results.json" ]; then
    echo ""
    echo "✅ Validation suite completed successfully!"
    
    # Move results to timestamped directory
    mv validation_results.json "$RESULTS_DIR/"
    
    # Generate README report
    echo "📋 Generating comprehensive README report..."
    cd "$RESULTS_DIR"
    python3 ../generate_validation_readme.py
    
    if [ -f "VALIDATION_REPORT.md" ]; then
        echo "✅ Validation report generated successfully!"
        echo ""
        echo "📁 Results saved in: $RESULTS_DIR/"
        echo "📋 Main report: $RESULTS_DIR/VALIDATION_REPORT.md"
        echo "📄 Summary: $RESULTS_DIR/VALIDATION_SUMMARY.txt"
        echo "📊 Raw data: $RESULTS_DIR/validation_results.json"
        echo "📝 Logs: $RESULTS_DIR/validation_log.txt"
        echo ""
        
        # Show quick summary
        echo "🎯 QUICK SUMMARY:"
        echo "=================="
        if [ -f "VALIDATION_SUMMARY.txt" ]; then
            head -20 "VALIDATION_SUMMARY.txt"
        fi
        
        echo ""
        echo "📖 View full report: cat $RESULTS_DIR/VALIDATION_REPORT.md"
        echo "🌐 Or open in browser: open $RESULTS_DIR/VALIDATION_REPORT.md"
        
    else
        echo "❌ Failed to generate validation report"
        exit 1
    fi
    
else
    echo "❌ Validation suite failed to complete"
    echo "📝 Check logs in: $RESULTS_DIR/validation_log.txt"
    exit 1
fi

echo ""
echo "🎉 Validation suite completed successfully!"
echo "📊 All results are available in the $RESULTS_DIR/ directory"
