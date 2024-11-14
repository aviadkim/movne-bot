@echo off
echo Current Project Structure:
echo ========================
tree /F
echo.
echo Listing YAML files in config:
echo ===========================
dir /B /S *.yaml
echo.
echo Environment Check:
echo ================
echo Checking for .env file...
if exist .env (
    echo .env file found
) else (
    echo .env file NOT found
)
echo.
echo Python Files:
echo ============
dir /B /S *.py
pause
