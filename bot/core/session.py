import time
from bot.utils.logger import logger

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException



class Session:
    def __init__(self, browser):
        self.browser = browser

    def login(self, username, password):
        logger.info("Logging in.....Please wait :)  ", step="login", event="start")
        self.browser.get("https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin")
        try:
            # Check if we are already logged in or if login page appears
            if "feed" in self.browser.current_url:
                logger.info("Already logged in.", step="login", event="success")
                return


            user_field = self.browser.find_element(By.ID, "username")
            pw_field = self.browser.find_element(By.ID, "password")
            login_button = self.browser.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            
            user_field.send_keys(username)
            user_field.send_keys(Keys.TAB)
            time.sleep(2)
            pw_field.send_keys(password)
            time.sleep(2)
            login_button.click()
            time.sleep(15)
        except TimeoutException:
            logger.info("TimeoutException! Username/password field or login button not found", step="login", event="failure", exception_type="TimeoutException")
        except Exception as e:
            logger.error(f"Login failed or already logged in: {e}", step="login", event="failure", exception=e)

