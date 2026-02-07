from selenium.webdriver.common.keys import Keys
from bot.application.form_filler import wait_span_click
from bot.utils.logger import print_lg

def discard_application(driver, actions):
    """Discard an ongoing application (useful for dry runs or when stuck)."""
    try:
        actions.send_keys(Keys.ESCAPE).perform()
        # Use selector registry via wait_span_click
        wait_span_click(driver, 'modal_discard', 2)
        print_lg("Application discarded.")
    except Exception as e:
        print_lg(f"Failed to discard application: {e}")
