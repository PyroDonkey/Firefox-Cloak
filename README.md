# Cloak - Simplified Privacy for Firefox

<p align="center">
  <img src="images/cloak_logo.png" alt="Cloak Logo" width="150" height="150">
</p>

Cloak is designed to automatically enhance privacy and security settings for Mozilla Firefox. The script provides an out-of-the-box Firefox experience with robust security, anti-tracking, and privacy features, removing modern bloatware and data collection systems.

## Project Goal

The aim of Cloak is to create an easy way for users to install a Firefox configuration that provides enhanced security and privacy right out of the box. This project simplifies the process of modifying and applying numerous privacy-enhancing settings, making it accessible for users who want to prioritize their online privacy quickly and easily.

## Features

Cloak applies a single, robust privacy-enhancing configuration:

- **Enhanced Privacy Protection**: Enables Strict Enhanced Tracking Protection and Total Cookie Protection.
- **Telemetry & Data Collection Disabled**: Turns off all telemetry features to prevent data collection, including Firefox's new Privacy-Preserving Attribution (PPA) system.
- **AI Features Disabled**: Automatically disabled built-in AI chatbots, suggestive groupings, and automated context parsing.
- **HTTPS-Only Mode**: Enforces HTTPS connections in all windows and enables Encrypted Client Hello (ECH) for improved security.
- **DNS Protection**: Configures DNS-over-HTTPS settings and sets Quad9 as the DNS provider.
- **Password Security**: Disables Firefox's built-in password manager feature.
- **Search Privacy**: Disables search suggestions and sponsored contextual links for increased privacy.
- **New Tab Page**: Removes sponsored and curated content (like Pocket) from the new tab page.
- **Anti-Fingerprinting**: Activates stronger fingerprinting protection measures and query stripping to reduce online tracking.

## Usage

You can run the installation script directly from PowerShell. 

Ensure you open PowerShell as an Administrator, then paste the following command:

```powershell
irm "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/Install.ps1" | iex
```

### What the script does:
- Checks for and installs standard Firefox if not present.
- Closes any running instances of Firefox.
- Downloads and applies the robust `user.js` configuration.
- Cleans up legacy settings (`prefs.js`) to ensure a fresh, private start.

## Warnings

It is strongly recommended to run this program on a fresh installation of Windows without a heavily customized Firefox profile.

If you choose to run this script with an existing Firefox installation, please ensure you have backed up all important data and understand that your current Firefox configuration will be significantly altered. The script is designed to provide maximum privacy, and may override your personal preferences.

- This script significantly modifies your Firefox configuration and may affect your browsing experience or cause certain websites to not function as expected due to strict tracking protections.
- Some changes include stricter content blocking, fingerprinting protection, and changes to default search and new tab behaviors.
- **Important**: Please ensure you understand how installing these features will change your browsing experience before proceeding with the installation.

## Requirements

- Windows OS
- PowerShell
- Internet connection for downloading necessary files

## Recommendation: Password Managers and Extensions

After installation, it's strongly recommended to:
1. **Install uBlock Origin**: Since Cloak focuses strictly on Firefox's native configurations, installing a robust adblocker like uBlock Origin is highly recommended.
2. **Review Privacy Guides**: Information on selecting a robust password manager, as Firefox's internal password manager will be disabled: [The Best Password Managers to Protect Your Privacy and Security - Privacy Guides](https://www.privacyguides.org/en/passwords/)

## Contribution

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/PyroDonkey/Firefox-Cloak/issues) if you want to contribute.