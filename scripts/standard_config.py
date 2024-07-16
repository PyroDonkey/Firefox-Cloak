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

def handle_exception(exc_type, exc_value, exc_traceback):
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

log_dir = os.path.join(tempfile.gettempdir(), "firefox_config")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "firefox_config.log")
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file, 'w', 'utf-8'),
                        logging.StreamHandler()
                    ])

def install_requirements():
    requirements = ['psutil', 'requests']
    max_retries = 5
    retry_delay = 5

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

    for package in requirements:
        try:
            __import__(package)
        except ImportError as e:
            logging.error(f"Failed to import {package} after installation: {e}")
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
        return None, None

def validate_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logging.error(f"Error validating URL {url}: {str(e)}")
        return False

def fetch_url_content(url, content_type='text'):
    try:
        import requests
        response = requests.get(url)
        response.raise_for_status()
        if content_type == 'json':
            content = response.json()
        else:
            content = response.text
        logging.info(f"Successfully fetched content from {url}")
        return content
    except requests.RequestException as e:
        logging.error(f"Error fetching content from {url}: {str(e)}")
        return None

def create_policies_json(policies_dir, policies_content):
    try:
        os.makedirs(policies_dir, exist_ok=True)
        policies_file = os.path.join(policies_dir, "policies.json")
        if os.path.exists(policies_file):
            backup_file = policies_file + ".backup"
            shutil.copy2(policies_file, backup_file)
            logging.info(f"Backup created: {backup_file}")
        with open(policies_file, 'w', encoding='utf-8') as f:
            json.dump(policies_content, f, indent=2, ensure_ascii=False)
        
        logging.info(f"Policies configuration successfully written to {policies_file}")
        return True
    except Exception as e:
        logging.error(f"Error in create_policies_json: {str(e)}")
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
            return False
    return True

def main():
    logging.info("Main function started")
    try:
        if not install_requirements():
            logging.error("Failed to install required packages. Exiting.")
            return

        if is_firefox_running():
            logging.info("Closing Firefox...")
            close_firefox()
        
        if not is_firefox_installed():
            logging.info("Installing Firefox ESR...")
            install_firefox_esr()
        
        logging.info("Launching and closing Firefox...")
        launch_and_close_firefox()

        user_js_url = "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/user.js/standard/user.js"
        custom_user_js = fetch_url_content(user_js_url)
        if custom_user_js is None:
            logging.error("Failed to fetch user.js content. Exiting.")
            return

        profile_dir = find_firefox_profile()
        logging.info(f"Firefox profile directory found: {profile_dir}")
        
        user_js_path = os.path.join(profile_dir, 'user.js')
        prefs_js_path = os.path.join(profile_dir, 'prefs.js')

        backup_file(user_js_path)
        delete_file(prefs_js_path)
        write_custom_file(user_js_path, custom_user_js)

        logging.info(f"Custom user.js has been installed in {profile_dir}")

        policies_dir, firefox_dir = find_firefox_directories()
        if not policies_dir or not firefox_dir:
            logging.error("Failed to find required directories")
            return

        policies_url = "https://raw.githubusercontent.com/PyroDonkey/Firefox-Cloak/main/policies/policies.json"
        policies_content = fetch_url_content(policies_url, content_type='json')
        if policies_content is None:
            logging.error("Failed to fetch policies.json content. Exiting.")
            return

        if create_policies_json(policies_dir, policies_content) and create_distribution_ini(firefox_dir):
            logging.info("Firefox configuration update completed successfully")
            print("\nFirefox configuration has been updated.")
            print("Please restart Firefox for the changes to take effect.")
        else:
            logging.error("Failed to update Firefox configuration")

    except Exception as e:
        logging.error(f"Exception in main function: {e}")
        logging.error(traceback.format_exc())
    logging.info("Main function completed")

if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            if 'asadmin' not in sys.argv:
                script = os.path.abspath(sys.argv[0])
                params = ' '.join([script] + sys.argv[1:] + ['asadmin'])
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                sys.exit(0)
        
        main()
    except Exception as e:
        logging.error(f"Unhandled exception in main: {e}")
        logging.error(traceback.format_exc())
    finally:
        print(f"\nScript execution completed. Check the log file at {log_file} for details.")
        time.sleep(5)