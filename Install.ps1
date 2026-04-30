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

# Wait for Firefox to create profile if it was just installed
$firefoxDataDir = "$env:APPDATA\Mozilla\Firefox"
$profilesDir    = "$firefoxDataDir\Profiles"
$profilesIni    = "$firefoxDataDir\profiles.ini"

if (-not (Test-Path $profilesDir)) {
    Write-Host "No Firefox profiles found. Launching Firefox briefly to create one..." -ForegroundColor Yellow
    if (Test-Path $firefoxPath) {
        $proc = Start-Process -FilePath $firefoxPath -PassThru
        Start-Sleep -Seconds 8
        Stop-Process -Name firefox -Force -ErrorAction SilentlyContinue | Out-Null
        Start-Sleep -Seconds 2
    }
    else {
        Write-Error "Could not locate Firefox to generate a profile."
        exit
    }
}

# Resolve the active profile from profiles.ini
# Priority: [Install*] Default= > [Profile*] Default=1 > *.default-release folder
$targetProfilePath = $null
$installDefaultPath = $null
$flagDefaultPath    = $null

if (Test-Path $profilesIni) {
    $iniLines      = Get-Content $profilesIni
    $currentSection = ""
    $currentPath    = $null
    $isDefault      = $false
    $installDefault = $null

    foreach ($line in $iniLines) {
        if ($line -match '^\[([^\]]+)\]') {
            # Flush previous [Install*] section
            if ($currentSection -match '^Install' -and $installDefault) {
                $installDefaultPath = $installDefault
            }
            # Flush previous [Profile*] section
            if ($currentSection -match '^Profile' -and $isDefault -and $currentPath) {
                $flagDefaultPath = $currentPath
            }

            $currentSection = $Matches[1]
            $currentPath    = $null
            $isDefault      = $false
            $installDefault = $null
        }
        elseif ($line -match '^Path=(.+)' -and $currentSection -match '^Profile') {
            $rel = $Matches[1].Trim().Replace('/', '\')
            $currentPath = Join-Path $firefoxDataDir $rel
        }
        elseif ($line -match '^Default=1' -and $currentSection -match '^Profile') {
            $isDefault = $true
        }
        elseif ($line -match '^Default=(.+)' -and $currentSection -match '^Install') {
            $rel = $Matches[1].Trim().Replace('/', '\')
            $candidate = Join-Path $firefoxDataDir $rel
            if (Test-Path $candidate) {
                $installDefault = $candidate
            }
            else {
                $candidate = Join-Path $profilesDir (Split-Path $rel -Leaf)
                if (Test-Path $candidate) {
                    $installDefault = $candidate
                }
            }
        }
    }

    # Flush last section
    if ($currentSection -match '^Install' -and $installDefault) {
        $installDefaultPath = $installDefault
    }
    if ($currentSection -match '^Profile' -and $isDefault -and $currentPath) {
        $flagDefaultPath = $currentPath
    }
}

# Apply priority: [Install*] > Default=1 > *.default-release scan
if ($installDefaultPath -and (Test-Path $installDefaultPath)) {
    $targetProfilePath = $installDefaultPath
    Write-Host "Profile resolved via [Install*] section" -ForegroundColor DarkGray
}
elseif ($flagDefaultPath -and (Test-Path $flagDefaultPath)) {
    $targetProfilePath = $flagDefaultPath
    Write-Host "Profile resolved via Default=1 flag" -ForegroundColor DarkGray
}
else {
    Write-Host "Falling back to folder scan for *.default-release..." -ForegroundColor Yellow
    $targetProfilePath = (Get-ChildItem -Path $profilesDir -Directory |
        Where-Object { $_.Name -like "*.default-release" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1).FullName
}

if (-not $targetProfilePath -or -not (Test-Path $targetProfilePath)) {
    Write-Error "Could not find a valid Firefox profile. Open Firefox once, close it, then re-run this script."
    exit
}

$targetProfile = Get-Item $targetProfilePath
Write-Host "Target Profile: $($targetProfile.FullName)" -ForegroundColor Green

# 4. Download and Apply user.js
$userJsUrl  = "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/user.js/standard/user.js"
$userJsPath = Join-Path -Path $targetProfile.FullName -ChildPath "user.js"
$prefsJsPath = Join-Path -Path $targetProfile.FullName -ChildPath "prefs.js"

# Backup existing user.js
if (Test-Path $userJsPath) {
    $backupPath = "$userJsPath.bak"
    if (Test-Path $backupPath) { Remove-Item -Path $backupPath -Force }
    Rename-Item -Path $userJsPath -NewName "user.js.bak" -Force
    Write-Host "Backed up existing user.js to user.js.bak" -ForegroundColor Yellow
}

try {
    Invoke-WebRequest -Uri $userJsUrl -OutFile $userJsPath -UseBasicParsing
}
catch {
    Write-Error "Failed to download user.js configuration from GitHub."
    exit
}

# Verify downloaded file is valid JS
$jsContent = Get-Content $userJsPath -Raw
if ($jsContent -notmatch 'user_pref') {
    Write-Error "Downloaded user.js appears invalid (no user_pref calls found). Check the GitHub URL."
    exit
}

Write-Host "Successfully downloaded and applied new user.js" -ForegroundColor Green
Write-Host "  Location: $userJsPath" -ForegroundColor DarkGray

# Delete prefs.js so user.js settings take effect cleanly on next launch
if (Test-Path $prefsJsPath) {
    Remove-Item -Path $prefsJsPath -Force
    Write-Host "Cleared prefs.js to apply new settings cleanly" -ForegroundColor Yellow
}

Write-Host "----------------------------------" -ForegroundColor Cyan
Write-Host "Firefox-Cloak Installation Complete!" -ForegroundColor Green
Write-Host "You can now open Firefox. Enjoy your private browsing." -ForegroundColor Cyan
Write-Host "----------------------------------" -ForegroundColor Cyan

# 5. Launch Success Page
Write-Host "Launching Setup Wizard..." -ForegroundColor Yellow
$successHtmlUrl = "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/success.html"
$successHtmlPath = Join-Path -Path $env:TEMP -ChildPath "CloakSuccess.html"

try {
    Invoke-WebRequest -Uri $successHtmlUrl -OutFile $successHtmlPath -UseBasicParsing
    if (Test-Path $firefoxPath) {
        Start-Process -FilePath $firefoxPath -ArgumentList "`"$successHtmlPath`""
    } else {
        Start-Process -FilePath $successHtmlPath
    }
} catch {
    Write-Host "Could not load the stylized landing page. Installation is still complete." -ForegroundColor Yellow
}
