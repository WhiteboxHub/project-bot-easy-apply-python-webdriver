from selenium.common.exceptions import StaleElementReferenceException
import time
from bot.utils.logger import logger
from bot.utils.exceptions import NavigationException

def safe_action(action_func, locator_func, max_retries=3):
    """
    Executes action_func(element). If StaleElementReferenceException occurs,
    calls locator_func() to get a fresh element and retries.
    """
    attempt = 1
    while attempt <= max_retries:
        try:
            element = locator_func()
            return action_func(element)
        except StaleElementReferenceException:
            logger.warning(f"Stale element encountered, retrying...", step="safe_action", event="stale_retry", attempt=attempt)
            time.sleep(1)
            attempt += 1
        except Exception as e:
            # Let other exceptions propagate specifically or wrap?
            # For now propagate generally but maybe log context if needed.
            raise e
            
    logger.error("Failed to recover from stale element", step="safe_action", event="stale_abort")
    raise NavigationException("Failed to recover from StaleElementReferenceException")
