import os
import sys
import time
import undetected_chromedriver as uc
from selenium_stealth import stealth
from dotenv import load_dotenv

import pathlib

# Load environment variables
load_dotenv()

def find_default_profile_directory() -> str | None:
    '''
    Dynamically finds the default Google Chrome 'User Data' directory path
    across Windows, macOS, and Linux.
    '''
    home = pathlib.Path.home()
    if sys.platform.startswith('win'):
        paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Google\Chrome\User Data"),
        ]
    elif sys.platform.startswith('linux'):
        paths = [
            str(home / ".config" / "google-chrome"),
            str(home / ".var" / "app" / "com.google.Chrome" / "data" / ".config" / "google-chrome"),
        ]
    else:
        return None

    for path_str in paths:
        if os.path.exists(path_str):
            return path_str
    return None

def get_options(headless, user_data_dir, incognito, disable_extensions, proxy_url):
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    if user_data_dir:
        options.add_argument(f"--user-data-dir={user_data_dir}")
    if incognito:
        options.add_argument("--incognito")
    if disable_extensions:
        options.add_argument("--disable-extensions")
    if proxy_url:
        options.add_argument(f'--proxy-server={proxy_url}')
    return options

def init_driver(
    headless=False,
    user_data_dir=None,
    proxy_url=None,
    disable_extensions=False,
    incognito=False
):
    """
    Initialize an undetected chromedriver with stealth settings and optional proxy.
    """
    # Undetected Chromedriver initialization
    try:
        # Try to initialize normally first
        options = get_options(headless, user_data_dir, incognito, disable_extensions, proxy_url)
        driver = uc.Chrome(options=options, use_subprocess=True)
        return apply_stealth(driver)
    except Exception as e:
        error_msg = str(e)
        if "version of ChromeDriver only supports Chrome version" in error_msg:
            import re
            match = re.search(r"Current browser version is ([\d.]+)", error_msg)
            if match:
                detected_version = match.group(1).split('.')[0]
                print(f"Detected Chrome version {detected_version}. Retrying with version_main={detected_version}...")
                try:
                    # RE-CREATE OPTIONS because they cannot be reused
                    options = get_options(headless, user_data_dir, incognito, disable_extensions, proxy_url)
                    driver = uc.Chrome(options=options, use_subprocess=True, version_main=int(detected_version))
                    return apply_stealth(driver)
                except Exception as retry_e:
                    print(f"Retry failed: {retry_e}")
        
        print(f"Error initializing undetected-chromedriver: {e}")
        raise

def apply_stealth(driver):
    """Apply Selenium Stealth settings to the driver."""
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    return driver

def check_chrome_running():
    """
    Check if Chrome is already running to avoid profile locks.
    Only relevant if using a specific user_data_dir.
    """
    if sys.platform == "win32":
        output = os.popen('tasklist /FI "IMAGENAME eq chrome.exe"').read()
        if "chrome.exe" in output:
            return True
    else:
        output = os.popen('pgrep chrome').read()
        if output:
            return True
    return False
