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
                "DisableTelemetry": True,
                "Extensions": {
                    "Install": [
                        "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
                    ]
                },
                "ExtensionUpdate": True  # Ensure extensions can update
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
user_pref("app.shield.optoutstudies.enabled", false);
user_pref("browser.contentblocking.category", "strict");
user_pref("browser.discovery.enabled", false);
user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);
user_pref("browser.newtabpage.activity-stream.feeds.topsites", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);
user_pref("browser.newtabpage.activity-stream.feeds.snippets", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.addons", false);
user_pref("browser.newtabpage.activity-stream.asrouter.userprefs.cfr.features", false);
user_pref("browser.newtabpage.activity-stream.default.sites", "");
user_pref("browser.newtabpage.pinned", "[]");
user_pref("browser.safebrowsing.malware.enabled", false);
user_pref("browser.safebrowsing.phishing.enabled", false);
user_pref("dom.security.https_only_mode", true);
user_pref("dom.security.https_only_mode_ever_enabled", true);
user_pref("network.dns.disablePrefetch", true);
user_pref("network.http.referer.disallowCrossSiteRelaxingDefault.top_navigation", true);
user_pref("network.http.speculative-parallel-limit", 0);
user_pref("network.predictor.enabled", false);
user_pref("network.prefetch-next", false);
user_pref("network.trr.custom_uri", "https://dns.quad9.net/dns-query");
user_pref("network.trr.mode", 3);
user_pref("network.trr.uri", "https://dns.quad9.net/dns-query");
user_pref("privacy.annotate_channels.strict_list.enabled", true);
user_pref("privacy.clearOnShutdown.offlineApps", true);
user_pref("privacy.donottrackheader.enabled", true);
user_pref("privacy.fingerprintingProtection", true);
user_pref("privacy.partition.network_state.ocsp_cache", true);
user_pref("privacy.query_stripping.enabled", true);
user_pref("privacy.query_stripping.enabled.pbmode", true);
user_pref("privacy.resistFingerprinting", true);
user_pref("privacy.sanitize.sanitizeOnShutdown", true);
user_pref("privacy.trackingprotection.emailtracking.enabled", true);
user_pref("privacy.trackingprotection.enabled", true);
user_pref("privacy.trackingprotection.socialtracking.enabled", true);
user_pref("signon.rememberSignons", false);
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