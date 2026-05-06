#!/bin/bash
echo "Fixing Angular package.json in downloaded project..."
echo

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "ERROR: package.json not found in current directory"
    echo "Please run this script from the hotel-management-system directory"
    exit 1
fi

echo "Current directory: $(pwd)"
echo

# Backup the original file
cp package.json package.json.backup

# Remove the invalid @angular/common/http dependency
sed -i '/"@angular\/common\/http":/d' package.json

echo "Fixed package.json - removed invalid @angular/common/http dependency"
echo

# Verify the fix
if grep -q "@angular/common/http" package.json; then
    echo "ERROR: Still contains invalid dependency!"
else
    echo "SUCCESS: Invalid dependency removed!"
fi

echo
echo "Now try running: docker compose up -d"
echo