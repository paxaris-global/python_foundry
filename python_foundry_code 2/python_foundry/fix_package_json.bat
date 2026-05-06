@echo off
echo Fixing Angular package.json in downloaded project...
echo.

REM Navigate to the downloaded project directory
cd /d "%~dp0"

REM Check if we're in the right directory
if not exist "package.json" (
    echo ERROR: package.json not found in current directory
    echo Please run this script from the hotel-management-system directory
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

REM Backup the original file
copy package.json package.json.backup

REM Remove the invalid @angular/common/http dependency
powershell -Command "(Get-Content package.json) -replace '\"@angular/common/http\": \"\^18\.2\.0\",', '' | Set-Content package.json"

echo Fixed package.json - removed invalid @angular/common/http dependency
echo.

REM Verify the fix
echo Verifying fix...
powershell -Command "if ((Get-Content package.json) -match '@angular/common/http') { Write-Host 'ERROR: Still contains invalid dependency!' -ForegroundColor Red } else { Write-Host 'SUCCESS: Invalid dependency removed!' -ForegroundColor Green }"

echo.
echo Now try running: docker compose up -d
echo.

pause