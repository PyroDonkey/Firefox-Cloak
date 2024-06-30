import subprocess
import sys
import os
import shutil
import glob
import time
import logging
import winreg
import site
import json
import platform
import traceback
import ctypes
from urllib.parse import urlparse
import tempfile
import threading

# Error handling setup
def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# Get the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change the current working directory to the script's directory
os.chdir(script_dir)

# Add the script's directory to sys.path
sys.path.insert(0, script_dir)

# Set up logging
log_file = os.path.join(script_dir, "firefox_config.log")
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file, 'w', 'utf-8'),
                        logging.StreamHandler()
                    ])

# Add more logging for troubleshooting
logging.info(f"Current working directory: {os.getcwd()}")
logging.info(f"Script location: {os.path.abspath(__file__)}")

# Global variable to store user's search engine choice
user_choice = None

def get_user_preferences_with_timeout():
    global user_choice
    user_choice = 1  # Always set to 1 for DuckDuckGo
    return user_choice

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if sys.argv[-1] != 'asadmin':
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        return True
    return False

def install_requirements():
    requirements = ['psutil', 'requests', 'selenium']
    max_retries = 5
    retry_delay = 5

    logging.info(f"Python executable: {sys.executable}")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"sys.path: {sys.path}")

    for package in requirements:
        for attempt in range(max_retries):
            logging.info(f"Attempting to install {package} (Attempt {attempt + 1}/{max_retries})...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "--no-cache-dir", package])
                logging.info(f"{package} installed successfully.")
                break
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install {package}: {e}")
                if attempt < max_retries - 1:
                    logging.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logging.error(f"Failed to install {package} after {max_retries} attempts.")
                    return False

    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.insert(0, user_site)
        logging.info(f"Added user site-packages to sys.path: {user_site}")

    for package in requirements:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'Unknown')
            logging.info(f"Verified {package} is installed and importable. Version: {version}")
        except ImportError as e:
            logging.error(f"Failed to import {package} after installation: {e}")
            logging.error(f"Current sys.path: {sys.path}")
            return False

    logging.info("All required packages are installed and verified.")
    return True

def find_firefox_path():
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe") as key:
            return winreg.QueryValue(key, None)
    except WindowsError:
        return None

def is_firefox_running():
    import psutil
    return 'firefox.exe' in (p.name() for p in psutil.process_iter())

def close_firefox():
    import psutil
    for process in psutil.process_iter(['name']):
        if process.info['name'] == 'firefox.exe':
            process.terminate()
    psutil.wait_procs([p for p in psutil.process_iter() if p.name() == 'firefox.exe'], timeout=10)

def is_firefox_installed():
    return find_firefox_path() is not None

def install_firefox_esr():
    import requests
    url = "https://download.mozilla.org/?product=firefox-esr-latest&os=win64&lang=en-US"
    installer_path = os.path.join(tempfile.gettempdir(), "firefox_esr_installer.exe")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(installer_path, 'wb') as f:
            f.write(response.content)
        subprocess.run([installer_path, "-ms"], check=True)
    except Exception as e:
        logging.error(f"Failed to install Firefox ESR: {e}")
    finally:
        if os.path.exists(installer_path):
            os.remove(installer_path)

def launch_and_close_firefox():
    firefox_path = find_firefox_path()
    if firefox_path:
        subprocess.Popen(firefox_path)
        time.sleep(5)
        close_firefox()
    else:
        logging.error("Firefox executable not found.")

def find_firefox_profile():
    firefox_path = os.path.expanduser(r'~\AppData\Roaming\Mozilla\Firefox\Profiles')
    profiles = glob.glob(os.path.join(firefox_path, '*.default*'))
    if not profiles:
        raise Exception("No Firefox profile found")
    esr_profile = next((p for p in profiles if 'esr' in p), None)
    return esr_profile if esr_profile else profiles[0]

def backup_file(file_path):
    if os.path.exists(file_path):
        shutil.copy2(file_path, f"{file_path}.bak")
        logging.info(f"Backup created for {file_path}")

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)
        logging.info(f"Deleted {file_path}")

def write_custom_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    logging.info(f"Written custom content to {file_path}")

def find_firefox_directories():
    try:
        system = platform.system()
        if system == "Windows":
            firefox_dir = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Mozilla Firefox")
            policies_dir = os.path.join(firefox_dir, "distribution")
        elif system == "Linux":
            firefox_dir = "/usr/lib/firefox"
            policies_dir = "/etc/firefox/policies"
        elif system == "Darwin":  # macOS
            firefox_dir = "/Applications/Firefox.app/Contents/Resources"
            policies_dir = "/Library/Application Support/Mozilla/policies"
        else:
            logging.error(f"Unsupported operating system: {system}")
            return None, None
        return policies_dir, firefox_dir
    except Exception as e:
        logging.error(f"Error in find_firefox_directories: {str(e)}")
        logging.debug(traceback.format_exc())
        return None, None

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logging.error(f"Error validating URL {url}: {str(e)}")
        return False

def create_policies_json(policies_dir):
    try:
        additional_engines = [
            {
                "Name": "Brave",
                "URLTemplate": "https://search.brave.com/search?q={searchTerms}",
                "Method": "GET",
                "IconURL": "https://brave.com/static-assets/images/brave-favicon.png",
                "Alias": "@brave",
                "Description": "Search Brave"
            },
            {
                "Name": "Startpage",
                "URLTemplate": "https://www.startpage.com/do/search?q={searchTerms}",
                "Method": "GET",
                "IconURL": "https://www.startpage.com/sp/cdn/favicons/favicon--default.ico",
                "Alias": "@startpage",
                "Description": "Search Startpage"
            },
            {
                "Name": "Kagi",
                "URLTemplate": "https://kagi.com/search?q={searchTerms}",
                "Method": "GET",
                "IconURL": "https://kagi.com/favicon.ico",
                "Alias": "@kagi",
                "Description": "Search Kagi (Subscription)"
            }
        ]

        for engine in additional_engines:
            for url_key in ["IconURL", "URLTemplate"]:
                if not validate_url(engine[url_key]):
                    logging.error(f"Invalid URL for {engine['Name']}: {url_key}")
                    return False

        default_engine = "DuckDuckGo" if user_choice == 1 else additional_engines[user_choice - 2]["Name"]
        
        policies = {
            "policies": {
                "SearchEngines": {
                    "Add": additional_engines,
                    "Default": default_engine,
                    "Remove": ["Google", "Bing", "Amazon.com", "eBay"]
                },
                "SearchSuggestEnabled": False,
                "DisableFirefoxStudies": True,
                "DisableTelemetry": True
            }
        }

        os.makedirs(policies_dir, exist_ok=True)
        policies_file = os.path.join(policies_dir, "policies.json")

        if os.path.exists(policies_file):
            backup_file = policies_file + ".backup"
            shutil.copy2(policies_file, backup_file)
            logging.info(f"Backup created: {backup_file}")

        with open(policies_file, 'w', encoding='utf-8') as f:
            json.dump(policies, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Policies configuration successfully written to {policies_file}")
        return True
    except Exception as e:
        logging.error(f"Error in create_policies_json: {str(e)}")
        logging.debug(traceback.format_exc())
        return False

def create_distribution_ini(firefox_dir):
    if platform.system() != "Windows":
        try:
            config_file = os.path.join(firefox_dir, "distribution", "distribution.ini")
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                f.write("[Global]\n")
                f.write("id=Mozilla Firefox\n")
                f.write("version=1.0\n")
                f.write("about=Firefox ESR configuration\n")
                f.write("policies=true\n\n")
                f.write("[Install]\n")
                f.write("InstallDirectory=${InstallDirectory}\n")
                f.write("Default=true\n")
            logging.info(f"Created distribution.ini at {config_file}")
            return True
        except Exception as e:
            logging.error(f"Failed to create distribution.ini: {str(e)}")
            logging.debug(traceback.format_exc())
            return False
    return True

def main():
    logging.info("Main function started")
    try:
        global user_choice
        
        logging.info("Script started with administrator privileges")

        # Ask for search engine preference at the start
        user_choice = get_user_preferences_with_timeout()
        logging.info(f"User selected search engine choice: {user_choice}")

        if not install_requirements():
            logging.error("Failed to install required packages. Exiting.")
            return

        import psutil
        import requests
        from selenium import webdriver

        # Part 1: Install Firefox and set custom user.js
        if is_firefox_running():
            logging.info("Closing Firefox...")
            close_firefox()
        
        if not is_firefox_installed():
            logging.info("Installing Firefox ESR...")
            install_firefox_esr()
        
        logging.info("Launching and closing Firefox...")
        launch_and_close_firefox()

        # Custom content for user.js
        custom_user_js = """
user_pref("app.installation.timestamp", "133635439371819418");
user_pref("app.normandy.first_run", false);
user_pref("app.normandy.migrationsApplied", 12);
user_pref("app.normandy.user_id", "09203c12-baf3-498f-a173-a6bc6ff866a5");
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("app.update.auto.migrated", true);
user_pref("app.update.background.lastInstalledTaskVersion", 4);
user_pref("app.update.background.rolledout", true);
user_pref("app.update.lastUpdateTime.addon-background-update-timer", 1719077962);
user_pref("app.update.lastUpdateTime.background-update-timer", 1719077962);
user_pref("app.update.lastUpdateTime.browser-cleanup-thumbnails", 1719077962);
user_pref("app.update.lastUpdateTime.recipe-client-addon-run", 1719077870);
user_pref("app.update.lastUpdateTime.region-update-timer", 1719077962);
user_pref("app.update.lastUpdateTime.rs-experiment-loader-timer", 1719077932);
user_pref("app.update.lastUpdateTime.services-settings-poll-changes", 1719077962);
user_pref("app.update.lastUpdateTime.telemetry_modules_ping", 1719077992);
user_pref("app.update.lastUpdateTime.telemetry_untrustedmodules_ping", 0);
user_pref("app.update.lastUpdateTime.xpi-signature-verification", 1719077962);
user_pref("app.update.migrated.updateDir3.308046B0AF4A39CB", true);
user_pref("browser.bookmarks.addedImportButton", true);
user_pref("browser.bookmarks.restore_default_bookmarks", false);
user_pref("browser.contentblocking.category", "strict");
user_pref("browser.contextual-services.contextId", "{f011555e-d73a-4de9-ba91-6752b518f23a}");
user_pref("browser.discovery.enabled", false);
user_pref("browser.download.viewableInternally.typeWasRegistered.avif", true);
user_pref("browser.download.viewableInternally.typeWasRegistered.webp", true);
user_pref("browser.laterrun.bookkeeping.profileCreationTime", 1719077867);
user_pref("browser.laterrun.bookkeeping.sessionCount", 1);
user_pref("browser.laterrun.enabled", true);
user_pref("browser.launcherProcess.enabled", true);
user_pref("browser.migration.version", 147);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
user_pref("browser.newtabpage.activity-stream.discoverystream.rec.impressions", "{"565015006":1719077897921,"3569121975715394":1719077897918,"4035648476384632":1719077897919}");
user_pref("browser.newtabpage.activity-stream.discoverystream.spoc.impressions", "{"537859106":[1719077897921,1719077931841]}");
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.impressionId", "{d961a719-74e5-4fbf-8807-ac20110c8567}");
user_pref("browser.newtabpage.activity-stream.improvesearch.topSiteSearchShortcuts.havePinned", "google");
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.pinned", "[{"url":"https://google.com","label":"@google","searchTopSite":true}]");
user_pref("browser.newtabpage.storageVersion", 1);
user_pref("browser.pageActions.persistedActions", "{"ids":["bookmark"],"idsInUrlbar":["bookmark"],"idsInUrlbarPreProton":[],"version":1}");
user_pref("browser.pagethumbnails.storage_version", 3);
user_pref("browser.privacySegmentation.createdShortcut", true);
user_pref("browser.proton.toolbar.version", 3);
user_pref("browser.region.update.updated", 1719077868);
user_pref("browser.safebrowsing.provider.google4.lastupdatetime", "1719077910943");
user_pref("browser.safebrowsing.provider.google4.nextupdatetime", "1719079706943");
user_pref("browser.safebrowsing.provider.mozilla.lastupdatetime", "1719077871091");
user_pref("browser.safebrowsing.provider.mozilla.nextupdatetime", "1719099471091");
user_pref("browser.search.region", "CA");
user_pref("browser.sessionstore.upgradeBackup.latestBuildID", "20240618110440");
user_pref("browser.shell.mostRecentDateSetAsDefault", "1719078509");
user_pref("browser.startup.couldRestoreSession.count", 2);
user_pref("browser.startup.homepage_override.buildID", "20240618110440");
user_pref("browser.startup.homepage_override.mstone", "127.0.1");
user_pref("browser.startup.lastColdStartupCheck", 1719078509);
user_pref("browser.uiCustomization.state", "{"placements":{"widget-overflow-fixed-list":[],"unified-extensions-area":["_74145f27-f039-47ce-a470-a662b129930a_-browser-action"],"nav-bar":["back-button","forward-button","stop-reload-button","customizableui-special-spring1","urlbar-container","customizableui-special-spring2","save-to-pocket-button","downloads-button","fxa-toolbar-menu-button","unified-extensions-button","ublock0_raymondhill_net-browser-action"],"toolbar-menubar":["menubar-items"],"TabsToolbar":["firefox-view-button","tabbrowser-tabs","new-tab-button","alltabs-button"],"PersonalToolbar":["import-button","personal-bookmarks"]},"seen":["save-to-pocket-button","developer-button","ublock0_raymondhill_net-browser-action","_74145f27-f039-47ce-a470-a662b129930a_-browser-action"],"dirtyAreaCache":["nav-bar","PersonalToolbar","toolbar-menubar","TabsToolbar","unified-extensions-area"],"currentVersion":20,"newElementCount":2}");
user_pref("browser.urlbar.placeholderName", "DuckDuckGo");
user_pref("browser.urlbar.placeholderName.private", "DuckDuckGo");
user_pref("browser.urlbar.quicksuggest.migrationVersion", 2);
user_pref("browser.urlbar.quicksuggest.scenario", "history");
user_pref("browser.urlbar.recentsearches.lastDefaultChanged", "1719077969810");
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionPolicyAcceptedVersion", 2);
user_pref("datareporting.policy.dataSubmissionPolicyNotifiedTime", "1719077868802");
user_pref("distribution.iniFile.exists.appversion", "127.0.1");
user_pref("distribution.iniFile.exists.value", false);
user_pref("doh-rollout.disable-heuristics", true);
user_pref("doh-rollout.doneFirstRun", true);
user_pref("doh-rollout.home-region", "CA");
user_pref("doh-rollout.uri", "https://private.canadianshield.cira.ca/dns-query");
user_pref("dom.forms.autocomplete.formautofill", true);
user_pref("dom.push.userAgentID", "12459d9cbdc14ee0a7e691a8cb7e958b");
user_pref("dom.security.https_only_mode", true);
user_pref("dom.security.https_only_mode_ever_enabled", true);
user_pref("extensions.activeThemeID", "default-theme@mozilla.org");
user_pref("extensions.blocklist.pingCountVersion", 0);
user_pref("extensions.databaseSchema", 36);
user_pref("extensions.formautofill.creditCards.reauth.optout", "MDIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECKbYm7O7GTZbBAhOnPr02WXaYA==");
user_pref("extensions.getAddons.cache.lastUpdate", 1719077962);
user_pref("extensions.getAddons.databaseSchema", 6);
user_pref("extensions.lastAppBuildId", "20240618110440");
user_pref("extensions.lastAppVersion", "127.0.1");
user_pref("extensions.lastPlatformVersion", "127.0.1");
user_pref("extensions.pendingOperations", false);
user_pref("extensions.pictureinpicture.enable_picture_in_picture_overrides", true);
user_pref("extensions.quarantinedDomains.list", "autoatendimento.bb.com.br,ibpf.sicredi.com.br,ibpj.sicredi.com.br,internetbanking.caixa.gov.br,www.ib12.bradesco.com.br,www2.bancobrasil.com.br");
user_pref("extensions.systemAddonSet", "{"schema":1,"addons":{}}");
user_pref("extensions.ui.dictionary.hidden", true);
user_pref("extensions.ui.extension.hidden", false);
user_pref("extensions.ui.lastCategory", "addons://list/extension");
user_pref("extensions.ui.locale.hidden", true);
user_pref("extensions.ui.sitepermission.hidden", true);
user_pref("extensions.webcompat.enable_shims", true);
user_pref("extensions.webcompat.perform_injections", true);
user_pref("extensions.webcompat.perform_ua_overrides", true);
user_pref("extensions.webextensions.ExtensionStorageIDB.migrated.screenshots@mozilla.org", true);
user_pref("extensions.webextensions.ExtensionStorageIDB.migrated.uBlock0@raymondhill.net", true);
user_pref("extensions.webextensions.ExtensionStorageIDB.migrated.{74145f27-f039-47ce-a470-a662b129930a}", true);
user_pref("extensions.webextensions.uuids", "{"formautofill@mozilla.org":"04fd398f-548e-4eae-868c-9872a033697b","pictureinpicture@mozilla.org":"873f603c-a355-4e15-b8d0-210698238cf5","screenshots@mozilla.org":"76caa832-b870-48b7-871b-d5c384a7bacb","webcompat-reporter@mozilla.org":"c08392e7-4c47-49e5-8a34-c5a626f56f9f","webcompat@mozilla.org":"d814e3e2-bd1b-4758-aaca-39053a07781e","default-theme@mozilla.org":"37bc32ed-f5b9-4720-9e8f-9db0b8aad2cd","addons-search-detection@mozilla.com":"414b485b-8807-43f6-92a6-a62cfe885218","google@search.mozilla.org":"a17c3172-a737-479c-86e7-87b7242960fc","wikipedia@search.mozilla.org":"178b3e4b-2b4c-487d-94ae-74a7c0b6d296","bing@search.mozilla.org":"8dbbcbaa-5c63-4c83-b6c2-ca798878ee18","ddg@search.mozilla.org":"6c9928e5-4101-4d23-a6bc-37b0edc899c0","ebay@search.mozilla.org":"5ac57032-8dfc-4919-b252-5b82c86434e0","uBlock0@raymondhill.net":"88a9a130-5bc0-48fe-ada8-63b5b4af7c72","{74145f27-f039-47ce-a470-a662b129930a}":"0d313887-80e4-4884-95f8-c172ec34ce8b"}");
user_pref("gecko.handlerService.defaultHandlersVersion", 1);
user_pref("media.gmp-gmpopenh264.abi", "x86_64-msvc-x64");
user_pref("media.gmp-gmpopenh264.hashValue", "b667086ed49579592d435df2b486fe30ba1b62ddd169f19e700cd079239747dd3e20058c285fa9c10a533e34f22b5198ed9b1f92ae560a3067f3e3feacc724f1");
user_pref("media.gmp-gmpopenh264.lastDownload", 1719077962);
user_pref("media.gmp-gmpopenh264.lastInstallStart", 1719077962);
user_pref("media.gmp-gmpopenh264.lastUpdate", 1719077962);
user_pref("media.gmp-gmpopenh264.version", "2.3.2");
user_pref("media.gmp-manager.buildID", "20240618110440");
user_pref("media.gmp-manager.lastCheck", 1719078615);
user_pref("media.gmp-manager.lastEmptyCheck", 1719078615);
user_pref("media.gmp-widevinecdm.abi", "x86_64-msvc-x64");
user_pref("media.gmp-widevinecdm.hashValue", "59521f8c61236641b3299ab460c58c8f5f26fa67e828de853c2cf372f9614d58b9f541aae325b1600ec4f3a47953caacb8122b0dfce7481acfec81045735947d");
user_pref("media.gmp-widevinecdm.lastDownload", 1719077963);
user_pref("media.gmp-widevinecdm.lastInstallStart", 1719077962);
user_pref("media.gmp-widevinecdm.lastUpdate", 1719077963);
user_pref("media.gmp-widevinecdm.version", "4.10.2710.0");
user_pref("media.gmp.storage.version.observed", 1);
user_pref("media.hardware-video-decoding.failed", false);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.http.referer.disallowCrossSiteRelaxingDefault.top_navigation", true);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("network.predictor.enabled", false);
user_pref("network.prefetch-next", false);
user_pref("network.trr.custom_uri", "https://dns.quad9.net/dns-query");
user_pref("network.trr.mode", 3);
user_pref("network.trr.uri", "https://dns.quad9.net/dns-query");
user_pref("pdfjs.enabledCache.state", true);
user_pref("pdfjs.migrationVersion", 2);
user_pref("privacy.annotate_channels.strict_list.enabled", true);
user_pref("privacy.fingerprintingProtection", true);
user_pref("privacy.query_stripping.enabled", true);
user_pref("privacy.query_stripping.enabled.pbmode", true);
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.sanitize.pending", "[{"id":"newtab-container","itemsToClear":[],"options":{}}]");
user_pref("privacy.trackingprotection.emailtracking.enabled", true);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("privacy.trackingprotection.socialtracking.enabled", true);
user_pref("sanity-test.device-id", "0x000d");
user_pref("sanity-test.driver-version", "");
user_pref("sanity-test.running", false);
user_pref("sanity-test.version", "20240618110440");
user_pref("services.settings.blocklists.addons-bloomfilters.last_check", 1719077961);
user_pref("services.settings.blocklists.gfx.last_check", 1719077961);
user_pref("services.settings.clock_skew_seconds", 0);
user_pref("services.settings.last_etag", ""1719071831345"");
user_pref("services.settings.last_update_seconds", 1719077961);
user_pref("services.settings.main.addons-manager-settings.last_check", 1719077961);
user_pref("services.settings.main.anti-tracking-url-decoration.last_check", 1719077961);
user_pref("services.settings.main.cfr.last_check", 1719077961);
user_pref("services.settings.main.cookie-banner-rules-list.last_check", 1719077961);
user_pref("services.settings.main.devtools-compatibility-browsers.last_check", 1719077961);
user_pref("services.settings.main.devtools-devices.last_check", 1719077961);
user_pref("services.settings.main.doh-config.last_check", 1719077961);
user_pref("services.settings.main.doh-providers.last_check", 1719077961);
user_pref("services.settings.main.fingerprinting-protection-overrides.last_check", 1719077961);
user_pref("services.settings.main.hijack-blocklists.last_check", 1719077961);
user_pref("services.settings.main.language-dictionaries.last_check", 1719077961);
user_pref("services.settings.main.message-groups.last_check", 1719077961);
user_pref("services.settings.main.nimbus-desktop-experiments.last_check", 1719077961);
user_pref("services.settings.main.normandy-recipes-capabilities.last_check", 1719077961);
user_pref("services.settings.main.partitioning-exempt-urls.last_check", 1719077961);
user_pref("services.settings.main.password-recipes.last_check", 1719077961);
user_pref("services.settings.main.password-rules.last_check", 1719077961);
user_pref("services.settings.main.pioneer-study-addons-v1.last_check", 1719077961);
user_pref("services.settings.main.query-stripping.last_check", 1719077961);
user_pref("services.settings.main.search-config-icons.last_check", 1719077961);
user_pref("services.settings.main.search-config-overrides-v2.last_check", 1719077961);
user_pref("services.settings.main.search-config-overrides.last_check", 1719077961);
user_pref("services.settings.main.search-config-v2.last_check", 1719077961);
user_pref("services.settings.main.search-config.last_check", 1719077961);
user_pref("services.settings.main.search-default-override-allowlist.last_check", 1719077961);
user_pref("services.settings.main.search-telemetry-v2.last_check", 1719077961);
user_pref("services.settings.main.sites-classification.last_check", 1719077961);
user_pref("services.settings.main.top-sites.last_check", 1719077961);
user_pref("services.settings.main.translations-models.last_check", 1719077961);
user_pref("services.settings.main.translations-wasm.last_check", 1719077961);
user_pref("services.settings.main.url-classifier-skip-urls.last_check", 1719077961);
user_pref("services.settings.main.websites-with-shared-credential-backends.last_check", 1719077961);
user_pref("services.sync.clients.lastSync", "0");
user_pref("services.sync.declinedEngines", "");
user_pref("services.sync.engine.addresses.available", true);
user_pref("services.sync.globalScore", 0);
user_pref("services.sync.nextSync", 0);
user_pref("signon.management.page.os-auth.optout", "MDIEEPgAAAAAAAAAAAAAAAAAAAEwFAYIKoZIhvcNAwcECN0Ox/7j2ReXBAj4W75qBQLLZw==");
user_pref("signon.rememberSignons", false);
user_pref("toolkit.startup.last_success", 1719078508);
user_pref("toolkit.telemetry.cachedClientID", "c0ffeec0-ffee-c0ff-eec0-ffeec0ffeec0");
user_pref("toolkit.telemetry.pioneer-new-studies-available", true);
user_pref("toolkit.telemetry.previousBuildID", "20240618110440");
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("trailhead.firstrun.didSeeAboutWelcome", true);
user_pref("ui.osk.debug.keyboardDisplayReason", "IKPOS: Touch screen not found.");
        """

        profile_dir = find_firefox_profile()
        logging.info(f"Firefox profile directory found: {profile_dir}")
        
        user_js_path = os.path.join(profile_dir, 'user.js')
        prefs_js_path = os.path.join(profile_dir, 'prefs.js')
        
        logging.info(f"user.js path: {user_js_path}")
        logging.info(f"prefs.js path: {prefs_js_path}")

        backup_file(user_js_path)
        delete_file(prefs_js_path)
        write_custom_file(user_js_path, custom_user_js)

        logging.info(f"Custom user.js has been installed in {profile_dir}")

        # Part 2: Install policies and set default search engines
        policies_dir, firefox_dir = find_firefox_directories()
        if not policies_dir or not firefox_dir:
            logging.error("Failed to find required directories")
            return

        logging.info(f"Policies directory: {policies_dir}")
        logging.info(f"Firefox directory: {firefox_dir}")

        if create_policies_json(policies_dir) and create_distribution_ini(firefox_dir):
            logging.info("Firefox configuration update completed successfully")
            print("\nFirefox search engine configuration has been updated.")
            print("Enterprise policies have been enabled.")
            print("Please restart Firefox for the changes to take effect.")
        else:
            logging.error("Failed to update Firefox configuration")

    except Exception as e:
        logging.error(f"Exception in main function: {e}")
        logging.error(traceback.format_exc())
    logging.info("Main function completed")

if __name__ == "__main__":
    try:
        if platform.system() == "Windows" and not is_admin():
            if 'asadmin' not in sys.argv:
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                print("Requesting administrator privileges...")
                sys.exit(0)
            else:
                print("Running with administrator privileges...")
        
        main()
    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
        logging.error(traceback.format_exc())
    finally:
        print("\nScript execution completed. Check the firefox_config.log file for details.")
        print("\nConfiguration complete! Enjoy your private Firefox experience.")
        print("This window will close in 30 seconds...")
        time.sleep(30)