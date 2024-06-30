# Cloak - A simple privacy script for Firefox

<p align="center">
  <img src="cloak_logo.png" alt="Cloak Logo" width="150" height="150">
</p>

Cloak is designed to enhance privacy and security settings for Firefox ESR (Extended Support Release). It automates the installation process and applies a strict configuration to protect user privacy, providing an out-of-the-box Firefox experience with robust security and privacy features.

## Project Goal

The aim of Cloak is to create an easy way for users to install a Firefox configuration that provides maximum security and privacy right out of the box. This project simplifies the process of modifying and applying numerous privacy-enhancing settings, making it accessible for users who want to prioritize their online privacy quickly and easily.

## Features

The `strict_config.py` script applies the following privacy-enhancing configurations:

- **Enhanced Privacy Protection**: Enables Strict Enhanced Tracking Protection for robust defense against trackers.
- **Cookie Management**: Automatically deletes cookies and site data when Firefox is closed.
- **Telemetry Disabled**: Turns off all telemetry features to prevent data collection.
- **HTTPS-Only Mode**: Enforces HTTPS connections in all windows for improved security.
- **DNS Protection**: Configures maximum protection DNS settings and sets Quad9 as the DNS provider.
- **Password Security**: Disables Firefox's built-in password manager feature as dedicated password manager software has better privacy and security features 
- **Search Privacy**: 
  - Disables search suggestions for increased privacy.
  - Sets DuckDuckGo as the default search engine.
  - Adds Brave, Startpage, and Kagi (subscription required) as privacy-focused search options.
  - Removes Google, Bing, and eBay from search shortcuts.
- **Anti-Fingerprinting**: Activates fingerprinting protection measures to reduce online tracking.
- **New Tab Page**: Removes sponsored and curated content from the new tab page.

## Scripts

### 1. Windows Installer (Windows Installer.bat)

This batch script automates the setup process on Windows:

- Checks for and installs Python 3.11+ if not present
- Installs Firefox ESR if not already installed
- Downloads and runs the `strict_config.py` script
- Handles user confirmation and provides warnings about the changes

### 2. Strict Configuration (strict_config.py)

This Python script installs Firefox ESR and automatically applies the privacy-enhancing configurations listed in the Features section.

## Usage

1. Download the `Windows Installer.bat` file.
2. Right-click the file and select "Run as administrator".
3. Follow the on-screen prompts to confirm the installation.

<span style="color: red;">## Warnings</span>

It is strongly recommended to run this program on a fresh installation of Windows without Firefox pre-installed. Running the script on an existing Firefox installation may:

- Cause unexpected issues
- Remove important user data or configurations
- Overwrite existing settings

If you choose to run this script with an existing Firefox installation, please ensure you have backed up all important data and understand that your current Firefox configuration will be significantly altered. The script is designed to work with a clean installation of Firefox ESR and may not function as intended with modified or pre-configured versions.

- This script significantly modifies your Firefox configuration and may affect your browsing experience.
- Some changes include stricter content blocking, fingerprinting protection, and changes to default search and new tab behaviors.
- This script is not compatible with the Rapid Release version of Firefox.
- **Important**: Please ensure you understand how installing these features will change your browsing experience before proceeding with the installation.
- This script is designed to work only with official versions of Firefox. Use with modified or unofficial versions is not supported and may lead to unexpected results.

## Requirements

- Windows operating system
- Administrator privileges
- Internet connection for downloading necessary files
- Official version of Firefox ESR

## Logging

The script creates log files in the `%Temp%\firefox_config` directory. Check these logs for detailed information about the installation process and any potential issues.

## Password Manager Recommendation

After installation, it's strongly recommended to review Privacy Guides for information on selecting a robust password manager as Firefox's password manager will be disabled: [Privacy Guides Password Managers](https://www.privacyguides.org/en/passwords/)

## Contribution

Contributions, issues, and feature requests are welcome. Feel free to check [issues page]([link-to-your-issues-page](https://github.com/PyroDonkey/Firefox-Cloak/issues)) if you want to contribute.
