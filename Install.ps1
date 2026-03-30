# Firefox-Cloak Install Script
# Designed to be run via: irm "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/Install.ps1" | iex

Write-Host "----------------------------------" -ForegroundColor Cyan
Write-Host "Starting Firefox-Cloak Installation..." -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan

# 1. Check for Firefox Installation
$firefoxInstalled = $false
$firefoxPath = ""

# Check Registry for Application Path
$regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"
if (Test-Path $regPath) {
    $firefoxPath = (Get-ItemProperty $regPath).'(default)'
    if ($firefoxPath -and (Test-Path $firefoxPath)) {
        $firefoxInstalled = $true
    }
}

# Fallback check
if (-not $firefoxInstalled) {
    $fallbackPaths = @(
        "$env:ProgramFiles\Mozilla Firefox\firefox.exe",
        "${env:ProgramFiles(x86)}\Mozilla Firefox\firefox.exe",
        "$env:LOCALAPPDATA\Mozilla Firefox\firefox.exe"
    )
    foreach ($path in $fallbackPaths) {
        if (Test-Path $path) {
            $firefoxInstalled = $true
            $firefoxPath = $path
            break
        }
    }
}

if (-not $firefoxInstalled) {
    Write-Host "Firefox is not installed. Downloading and installing..." -ForegroundColor Yellow
    $installerPath = Join-Path -Path $env:TEMP -ChildPath "Firefox Installer.exe"
    $downloadUrl = "https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=en-US"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
    }
    catch {
        Write-Error "Failed to download Firefox installer. Please check your internet connection."
        exit
    }
    
    Write-Host "Installing Firefox silently (this may take a minute)..." -ForegroundColor Yellow
    $process = Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -PassThru
    
    if ($process.ExitCode -eq 0 -or (Test-Path "$env:ProgramFiles\Mozilla Firefox\firefox.exe")) {
        Write-Host "Firefox installed successfully." -ForegroundColor Green
        $firefoxPath = "$env:ProgramFiles\Mozilla Firefox\firefox.exe"
    }
    else {
        Write-Error "Failed to install Firefox. Please install it manually and run this script again."
        exit
    }
    
    # Clean up installer
    if (Test-Path $installerPath) { Remove-Item -Path $installerPath -Force }
}
else {
    Write-Host "Firefox is already installed at: $firefoxPath" -ForegroundColor Green
}

# 2. Close Firefox if running
$firefoxProcess = Get-Process firefox -ErrorAction SilentlyContinue
if ($firefoxProcess) {
    Write-Host "Closing Firefox..." -ForegroundColor Yellow
    Stop-Process -Name firefox -Force -ErrorAction SilentlyContinue | Out-Null
    Start-Sleep -Seconds 3
}

# 3. Apply Configuration
Write-Host "Applying Privacy and Security Configurations..." -ForegroundColor Cyan

# Wait for Firefox to create profile if it was just installed (launch and close)
$profilesDir = "$env:APPDATA\Mozilla\Firefox\Profiles"
if (-not (Test-Path $profilesDir) -or (Get-ChildItem -Path $profilesDir -Filter "*.default*" | Measure-Object).Count -eq 0) {
    Write-Host "No Firefox profiles found. Launching Firefox briefly to create one..." -ForegroundColor Yellow
    
    if (Test-Path $firefoxPath) {
        Start-Process -FilePath $firefoxPath
        Start-Sleep -Seconds 5
        Stop-Process -Name firefox -Force -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 2
    }
    else {
        Write-Error "Could not start Firefox to generate a profile."
        exit
    }
}

$profiles = Get-ChildItem -Path $profilesDir -Directory | Where-Object { $_.Name -like "*.default-release*" -or $_.Name -like "*.default*" }

if ($profiles.Count -eq 0) {
    Write-Error "Could not find a valid Firefox profile. Please open Firefox once manually, close it, and try again."
    exit
}

# Pick the first matching profile (Prefer default-release)
$targetProfile = $profiles | Sort-Object { $_.Name -match "default-release" } -Descending | Select-Object -First 1
Write-Host "Target Profile: $($targetProfile.FullName)" -ForegroundColor Green

# 4. Download and Apply user.js
$userJsUrl = "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/user.js/standard/user.js"
$userJsPath = Join-Path -Path $targetProfile.FullName -ChildPath "user.js"
$prefsJsPath = Join-Path -Path $targetProfile.FullName -ChildPath "prefs.js"

# Backup existing user.js
if (Test-Path $userJsPath) {
    $backupPath = "$userJsPath.bak"
    # Overwrite old backup if exists
    if (Test-Path $backupPath) { Remove-Item -Path $backupPath -Force }
    Rename-Item -Path $userJsPath -NewName "user.js.bak" -Force
    Write-Host "Backed up existing user.js to user.js.bak" -ForegroundColor Yellow
}

try {
    Invoke-WebRequest -Uri $userJsUrl -OutFile $userJsPath -UseBasicParsing
    Write-Host "Successfully downloaded and applied new user.js" -ForegroundColor Green
}
catch {
    Write-Error "Failed to download user.js configuration from GitHub."
    exit
}

# Delete prefs.js so user.js takes precedence on next launch
if (Test-Path $prefsJsPath) {
    Remove-Item -Path $prefsJsPath -Force
    Write-Host "Cleared prefs.js to apply new settings cleanly" -ForegroundColor Yellow
}

Write-Host "----------------------------------" -ForegroundColor Cyan
Write-Host "Firefox-Cloak Installation Complete!" -ForegroundColor Green
Write-Host "You can now open Firefox. Enjoy your private browsing." -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan
