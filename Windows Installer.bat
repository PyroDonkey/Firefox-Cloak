@echo off
setlocal enabledelayedexpansion

echo WARNING: This script will perform the following actions:
echo 1. Install Python if not already installed
echo 2. Install Firefox ESR if not already installed
echo 3. Download and run a script to create a new user.js file with custom Firefox settings, including:
echo    - Disabling telemetry and data collection
echo    - Enhancing privacy and security settings
echo    - Configuring DNS-over-HTTPS
echo    - Adjusting content blocking and tracking protection
echo    - Modifying new tab page behavior
echo    - Setting DuckDuckGo as the default search engine
echo    - Enabling HTTPS-only mode
echo 4. Launch and close Firefox to apply settings
echo.
echo These actions will significantly modify your Firefox configuration and may affect your browsing experience.
echo Some changes include stricter content blocking, fingerprinting protection, and changes to default search and new tab behaviors.
echo This script is not compatible with the Rapid Release version of Firefox.
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

:: Check if Python 3.11 or higher is installed
for /f "tokens=*" %%i in ('python -c "import sys; print(sys.version_info >= (3, 11))"') do set "python_check=%%i"

if "%python_check%"=="True" (
    echo Python 3.11 or higher is already installed.
    for /f "tokens=*" %%i in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_PATH=%%i"
    echo Using Python at: !PYTHON_PATH!
) else (
    echo Python 3.11 or higher is not installed. Proceeding with installation...

    :: Download Python installer
    echo Downloading Python 3.11 installer...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe', '%temp_dir%\python_installer.exe')"
    if %errorlevel% neq 0 (
        echo Failed to download Python installer.
        goto Cleanup
    )

    :: Install Python silently
    echo Installing Python 3.11...
    start /wait "" "%temp_dir%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    if %errorlevel% neq 0 (
        echo Failed to install Python.
        goto Cleanup
    )

    :: Set the direct path to the Python executable
    set "PYTHON_PATH=C:\Program Files\Python311\python.exe"

    :: Verify installation using direct path
    echo Verifying Python installation...
    "%PYTHON_PATH%" --version
    if %errorlevel% neq 0 (
        echo Python installation failed or Python is not in the expected location.
        goto Cleanup
    )
)

:: Verify Python version
for /f "tokens=2" %%V in ('"%PYTHON_PATH%" -V 2^>^&1') do set PYTHON_VERSION=%%V
echo Using Python version: %PYTHON_VERSION%

:: Download and run the Python script from GitHub
echo Downloading strict_config.py from GitHub...
powershell -Command "(New-Object Net.WebClient).DownloadFile('https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/scripts/strict_config.py', '%temp_dir%\strict_config.py')"
if %errorlevel% neq 0 (
    echo Failed to download strict_config.py from GitHub.
    goto Cleanup
)

echo Running strict_config.py...
"%PYTHON_PATH%" "%temp_dir%\strict_config.py"
if %errorlevel% neq 0 (
    echo Failed to run strict_config.py.
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