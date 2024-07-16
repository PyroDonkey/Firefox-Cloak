@echo off
setlocal enabledelayedexpansion

:: Define the Python install directory
set "PYTHON_INSTALL_DIR=C:\Program Files\Python"

echo WARNING: This script will perform the following actions:
echo 1. Install Python if not already installed
echo 2. Install Firefox ESR if not already installed
echo 3. Modify your Firefox profile settings, including:
echo    - Enhancing privacy and security settings
echo    - Disabling telemetry and data collection
echo    - Changing network and DNS configurations
echo    - Altering content and new tab behaviors
echo 4. Modify your search engine settings
echo 6. Install uBlock Origin
echo 7. Create or update Firefox policies, which may affect browser behavior
echo.
echo These actions will significantly modify your Firefox configuration and may impact your browsing experience.
echo Administrative privileges are required for some operations.
echo.
set /p CONFIRM=Do you want to proceed? (Y/N):

if /i "%CONFIRM%" neq "Y" (
    echo Operation cancelled by user.
    exit /b
)

echo Checking if Firefox is running...
tasklist /FI "IMAGENAME eq firefox.exe" 2>NUL | find /I /N "firefox.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Closing Firefox...
    taskkill /F /IM firefox.exe
)

echo Starting Python installation check and script execution process...

:: Set up temporary directory
set "temp_dir=%temp%\firefox_config"
mkdir "%temp_dir%" 2>nul

:: Check for any Python installation
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
    for /f "tokens=2" %%V in ('python -V 2^>^&1') do set "PYTHON_VERSION=%%V"
    echo Current Python version: %PYTHON_VERSION%
    set "PYTHON_PATH=python"
    goto ConfigSelection
)

echo Python is not installed. Proceeding with installation...

:: Set the URL for Python downloads page
set "url=https://www.python.org/downloads/"

:: Use PowerShell to fetch the latest version
echo Fetching latest Python version...
for /f "tokens=* usebackq" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$html = (Invoke-WebRequest -Uri '%url%' -UseBasicParsing).Content; if($html -match 'Download Python (\d+\.\d+\.\d+)') { $matches[1] }"`) do (
    set "version=%%a"
)

if not defined version (
    echo Failed to find the latest Python version.
    goto Cleanup
)

echo Latest Python version: %version%

:: Construct the download link
set "download_link=https://www.python.org/ftp/python/%version%/python-%version%-amd64.exe"

:: Download Python installer
echo Downloading Python %version% installer...
powershell -Command "(New-Object Net.WebClient).DownloadFile('%download_link%', '%temp_dir%\python_installer.exe')"
if %errorlevel% neq 0 (
    echo Failed to download Python installer.
    goto Cleanup
)

:: Install Python silently to the specified directory
echo Installing Python %version% to %PYTHON_INSTALL_DIR%...
start /wait "" "%temp_dir%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 TargetDir="%PYTHON_INSTALL_DIR%"
if %errorlevel% neq 0 (
    echo Failed to install Python.
    goto Cleanup
)

:: Verify Python installation
set "PYTHON_PATH=%PYTHON_INSTALL_DIR%\python.exe"
if not exist "%PYTHON_PATH%" (
    echo Python installation not found in %PYTHON_INSTALL_DIR%.
    goto Cleanup
)

echo Found Python at: %PYTHON_PATH%

:: Verify installation
echo Verifying Python installation...
"%PYTHON_PATH%" --version
if %errorlevel% neq 0 (
    echo Python installation failed or Python is not in the expected location.
    goto Cleanup
)

:ConfigSelection
:: Prompt user to choose between Strict and Standard configurations
echo.
echo Please choose a configuration:
echo 1. Standard (Recommended)
echo 2. Strict
set /p CONFIG_CHOICE=Enter your choice (1 or 2): 

if "%CONFIG_CHOICE%"=="1" (
    set "CONFIG_TYPE=standard"
    set "CONFIG_URL=https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/scripts/standard_config.py"
) else if "%CONFIG_CHOICE%"=="2" (
    set "CONFIG_TYPE=strict"
    set "CONFIG_URL=https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/scripts/strict_config.py"
) else (
    echo Invalid choice. Exiting.
    goto Cleanup
)

:RunScript
:: Verify Python version
for /f "tokens=2" %%V in ('"%PYTHON_PATH%" -V 2^>^&1') do set PYTHON_VERSION=%%V
echo Using Python version: %PYTHON_VERSION%

:: Download and run the selected Python script from GitHub
echo Downloading %CONFIG_TYPE%_config.py from GitHub...
powershell -Command "(New-Object Net.WebClient).DownloadFile('%CONFIG_URL%', '%temp_dir%\%CONFIG_TYPE%_config.py')"
if %errorlevel% neq 0 (
    echo Failed to download %CONFIG_TYPE%_config.py from GitHub.
    goto Cleanup
)

echo Running %CONFIG_TYPE%_config.py...
"%PYTHON_PATH%" "%temp_dir%\%CONFIG_TYPE%_config.py"
if %errorlevel% neq 0 (
    echo Failed to run %CONFIG_TYPE%_config.py.
    goto Cleanup
)

echo Script execution completed successfully.

:Cleanup
:: Clean up temporary files
if exist "%temp_dir%" (
    rmdir /s /q "%temp_dir%"
)

endlocal
exit /b