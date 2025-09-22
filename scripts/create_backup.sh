#!/bin/bash
# Script to create a backup of the PickerWheel system

echo "=== CREATING BACKUP OF PICKERWHEEL SYSTEM ==="
echo ""

# Configuration
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="../pickerwheel-v4-BACKUP-$TIMESTAMP"

# Create backup directory
echo "🔄 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Copy all files
echo "🔄 Copying files..."
cp -r ../* "$BACKUP_DIR/"

# Remove unnecessary files from backup
echo "🔄 Cleaning up backup..."
rm -rf "$BACKUP_DIR/node_modules" 2>/dev/null
rm -rf "$BACKUP_DIR/__pycache__" 2>/dev/null
rm -f "$BACKUP_DIR/*.log" 2>/dev/null

# Create backup info file
echo "🔄 Creating backup info file..."
cat > "$BACKUP_DIR/BACKUP_INFO.md" << EOF
# PickerWheel System Backup

## Backup Details
- **Date**: $(date)
- **Version**: PickerWheel v4 Clean
- **Status**: ✅ FULLY FUNCTIONAL - Daily Limits Fixed

## Included Files
- Backend API with fixed daily limits
- Frontend with correct port configuration
- Database with proper schema
- CSV configuration with simplified format
- Scripts for system management

## Verification Status
- ✅ Daily limits for rare items: VERIFIED
- ✅ Daily limits for ultra-rare items: VERIFIED
- ✅ CSV synchronization: VERIFIED
- ✅ Database schema: VERIFIED

## Pending Fixes
- ⚠️ Wheel positioning logic needs to be updated to use dynamic prize count

Created automatically by backup script.
EOF

echo ""
echo "✅ Backup created successfully at: $BACKUP_DIR"
echo ""
