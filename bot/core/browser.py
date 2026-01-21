import os
import logging
import platform
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.options import Options


log = logging.getLogger(__name__)

class Browser:
    def __init__(self, profile_path=None):
        self.profile_path = profile_path
        self.driver = self._setup_driver()

    def _setup_driver(self):
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-extensions")
        
        # Disable webdriver flags
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Cross-platform profile detection if not provided
        if not self.profile_path:
            system_name = platform.system()
            if system_name == 'Darwin':
                self.profile_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
            elif system_name == 'Linux':
                self.profile_path = os.path.expanduser("~/.config/google-chrome")
            elif system_name == 'Windows':
                self.profile_path = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')
        
        if self.profile_path:
             log.info(f"Using profile path: {self.profile_path}")
             options.add_argument(f'--user-data-dir={self.profile_path}')
             options.add_argument('--profile-directory=Default')

        driver = uc.Chrome(options=options, use_subprocess=True)
        
        # Apply stealth settings
        # Determine platform string for stealth match
        system_name = platform.system()
        stealth_platform = "Win32" # Default fallback
        if system_name == 'Darwin':
            stealth_platform = "MacIntel"
        elif system_name == 'Linux':
            stealth_platform = "Linux x86_64"
            
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform=stealth_platform,
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        return driver

