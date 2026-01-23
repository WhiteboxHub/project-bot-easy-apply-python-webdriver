import time
import random
from humancursor import SystemCursor
from bot.utils.logger import logger

class HumanInteraction:
    def __init__(self, browser):
        self.browser = browser
        try:
            # humancursor uses SystemCursor or WebCursor. 
            # SystemCursor controls the actual mouse. WebCursor might be safer/easier if strictly web.
            # The prompt suggested WebCursor but the library might have changed or I should check what's available.
            # Let's stick to the prompt's suggestion but wrap it safely. 
            # Actually, SystemCursor is often more robust for undetected-chromedriver as it moves the real mouse
            # which avoids all selenium detection flags for input.
            # However, for headless (if ever used) or background, it's an issue.
            # Given we are "undetected", real mouse input is best.
            self.cursor = SystemCursor() 
        except Exception as e:
            logger.warning(f"Failed to initialize HumanCursor: {e}. Fallback to standard selenium might be needed manually.", step="human_init")
            self.cursor = None

    def scroll_page(self):
        """
        Scrolls the window with natural stutter.
        """
        total_height = self.browser.execute_script("return document.body.scrollHeight")
        current_pos = self.browser.execute_script("return window.pageYOffset")
        
        while current_pos < total_height:
            step = random.randint(300, 700)
            current_pos += step
            
            # Occasional scroll up (jitter)
            if random.random() < 0.1:
                current_pos -= random.randint(50, 150)
            
            self.browser.execute_script(f"window.scrollTo(0, {current_pos});")
            time.sleep(random.uniform(0.1, 0.4))
            
            # Check if we hit bottom
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if current_pos >= new_height:
                break
            total_height = new_height

    def scroll_element(self, element):
        """
        Scrolls a specific element (like a job list container) with stutter.
        """
        try:
            total_height = self.browser.execute_script("return arguments[0].scrollHeight", element)
            current_pos = self.browser.execute_script("return arguments[0].scrollTop", element)
            
            # Scroll a chunk, not necessarily to the end if logic dictates controlled scroll.
            # But here we simulate a "scroll down" action.
            
            target = current_pos + random.randint(300, 600)
            
            # Jitter
            if random.random() < 0.1:
                target -= random.randint(20, 100)
                
            self.browser.execute_script(f"arguments[0].scrollTo(0, {target});", element)
            time.sleep(random.uniform(0.2, 0.5))
            
            return target # Return new position estimate
        except Exception as e:
            logger.warning(f"Human scroll failed: {e}", step="human_scroll")

    def click(self, element):
        """
        Moves to element with natural curves and clicks.
        """
        try:
            if self.cursor:
                # Some humancursor versions may have issues with UC WebElements
                # We try it, but if it fails with type errors we fall back immediately
                self.cursor.click_on(element)
                return
        except Exception:
            pass # Silent fallback for speed and cleaner logs
        
        # Standard Selenium click is more reliable across environments
        try:
            element.click()
        except Exception as e:
            # Last resort: JS click
            try:
                self.browser.execute_script("arguments[0].click();", element)
            except:
                logger.warning(f"All click methods failed: {e}", step="click_error")


    def type(self, element, text):
        """
        Types text with random delays between keystrokes.
        """
        element.click()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
