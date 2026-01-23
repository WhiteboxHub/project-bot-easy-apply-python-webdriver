import os
import logging
import platform
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.chrome.options import Options


log = logging.getLogger(__name__)

class Browser:
    def __init__(self, profile_path=None, proxy_config=None):
        self.profile_path = profile_path
        self.proxy_config = proxy_config
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
        # CHANGED: Don't use default profile automatically - use guest mode instead
        # This prevents conflicts with existing Chrome instances
        if self.profile_path:
             log.info(f"Using profile path: {self.profile_path}")
             options.add_argument(f'--user-data-dir={self.profile_path}')
             options.add_argument('--profile-directory=Default')
        else:
             log.info("Using guest mode (no profile persistence)")
             # Guest mode - won't conflict with existing Chrome
             options.add_argument('--guest')
        
        # Add proxy configuration if provided
        if self.proxy_config:
            proxy_string = self.proxy_config.get_chrome_proxy_string()
            options.add_argument(f'--proxy-server={proxy_string}')
            log.info(f"Using proxy: {self.proxy_config.name} ({proxy_string})")
            
            # If proxy has authentication, we need to handle it via extension
            if self.proxy_config.username and self.proxy_config.password:
                log.info("Proxy authentication will be handled via Chrome extension")

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

