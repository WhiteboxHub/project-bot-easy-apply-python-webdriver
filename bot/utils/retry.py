import functools
import logging
from time import sleep

logger = logging.getLogger("LinkedInBot")

def retry(max_attempts=3, delay=2, exceptions=(Exception,)):
    """
    Decorator to retry a function if it fails.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts. Error: {e}")
                        raise
                    logger.warning(f"Attempt {attempts} failed for {func.__name__}. Retrying in {delay}s... Error: {e}")
                    sleep(delay)
            return None
        return wrapper
    return decorator
