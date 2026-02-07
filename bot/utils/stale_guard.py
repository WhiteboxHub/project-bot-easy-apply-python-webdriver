from selenium.common.exceptions import StaleElementReferenceException
from bot.utils.retry import retry

@retry(max_attempts=3, exceptions=(StaleElementReferenceException,))
def safe_click(element):
    """Click an element with Staleness protection."""
    element.click()

@retry(max_attempts=3, exceptions=(StaleElementReferenceException,))
def get_text_safe(element):
    """Get text from an element with Staleness protection."""
    return element.text
