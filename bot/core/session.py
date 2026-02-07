from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bot.application.form_filler import text_input_by_ID, find_by_class, try_linkText, try_xp, wait_span_click
from bot.utils.logger import print_lg, log_step
from time import sleep
import pyautogui

from bot.utils.selectors import Selectors, SelectorRegistry


def _url_indicates_logged_out(url: str) -> bool:
    u = (url or "").lower()
    return any(p in u for p in ["/login", "/authwall", "/checkpoint", "/signup"])


def _has_login_form(driver) -> bool:
    # Explicit login form markers on LinkedIn pages
    return bool(
        try_xp(driver, "//input[@id='username' or @name='session_key']", False)
        or try_xp(driver, "//input[@id='password' or @name='session_password']", False)
        or try_xp(driver, "//button[@type='submit' and (contains(., 'Sign in') or contains(., 'Log in'))]", False)
    )

def is_logged_in_LN(driver):
    '''
    Function to check if user is logged-in in LinkedIn
    '''
    print_lg("🔍 Checking if logged in...")
    # Open LinkedIn if driver is on a blank/non-linkedin page
    if "linkedin.com" not in (driver.current_url or ""):
        driver.get("https://www.linkedin.com/")
        sleep(2)

    current_url = driver.current_url
    if _url_indicates_logged_out(current_url):
        print_lg(f"❌ Not logged in (URL indicates logged-out state): {current_url}")
        return False

    # Strong signal: authenticated session cookie exists
    li_at_cookie = driver.get_cookie("li_at")
    if li_at_cookie:
        print_lg("✅ Session cookie detected (li_at)")
    
    # 2. Logged-in Indicators
    indicators = {
        "Me Avatar": "//button[contains(@class, 'global-nav__primary-link') and contains(., 'Me')]",
        "Settings Dropdown": "//div[contains(@id, 'nav-settings__dropdown')]",
        "Logout Link": "//a[contains(@href, '/logout/')]",
        "Home Link": "//span[contains(@class, 'global-nav__primary-link-text') and contains(text(), 'Home')]"
    }
    for name, xpath in indicators.items():
        if try_xp(driver, xpath, False):
            print_lg(f"✅ Logged in (Detected: {name})")
            return True

    # 3. Logged-out Indicators
    logged_out_indicators = {
        "Sign In Button (Nav)": Selectors.SIGN_IN_LANDING_BUTTON, 
        "Sign In Modal": Selectors.SIGN_IN_MODAL,
        "Login Link": "//a[contains(@href, 'login')]",
        "Sign in Text (Button)": "//button[contains(text(), 'Sign in')]",
        "Log in Text (Button)": "//button[contains(text(), 'Log in')]",
        "Join now Link": "//a[contains(text(), 'Join now')]"
    }
    for name, xpath in logged_out_indicators.items():
        if try_xp(driver, xpath, False):
            print_lg(f"❌ Not logged in (Detected: {name})")
            return False

    if _has_login_form(driver):
        print_lg("❌ Not logged in (Login form fields detected)")
        return False

    # 4. Final guess - check if we are on a login page already
    if _url_indicates_logged_out(driver.current_url):
        return False

    print_lg("⚠️ Login state ambiguous. Testing feed access...")
    driver.get("https://www.linkedin.com/feed/")
    sleep(3)

    feed_url = driver.current_url
    if _url_indicates_logged_out(feed_url) or _has_login_form(driver):
        print_lg(f"❌ Not logged in (Feed redirected/authwall): {feed_url}")
        return False

    if "linkedin.com/feed" in feed_url and (
        driver.get_cookie("li_at") or try_xp(driver, indicators["Home Link"], False)
    ):
        print_lg("✅ Logged in (Feed + session markers verified)")
        return True

    print_lg(f"❌ Not logged in (Ambiguous feed state): {feed_url}")
    return False

def login_LN(driver, wait, username, password):
    '''
    Function to login for LinkedIn
    '''
    driver.get("https://www.linkedin.com/login")
    try:
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, Selectors.FORGOT_PASSWORD_LINK_TEXT)))
        try:
            text_input_by_ID(driver, Selectors.LOGIN_USERNAME_ID, username, 1)
        except Exception as e:
            print_lg("Couldn't find username field.")
        try:
            text_input_by_ID(driver, Selectors.LOGIN_PASSWORD_ID, password, 1)
        except Exception as e:
            print_lg("Couldn't find password field.")
        
        # Try clicking via registry
        if not wait_span_click(driver, "login_submit", 2):
            driver.find_element(By.XPATH, Selectors.LOGIN_SUBMIT_BUTTON).click()
            
    except Exception as e1:
        try:
            profile_button = find_by_class(driver, "profile__details")
            profile_button.click()
        except Exception as e2:
            print_lg("Couldn't Login via UI, maybe already logged in or needs manual intervention.")

    try:
        wait.until(lambda d: "linkedin.com" in (d.current_url or "") and not _url_indicates_logged_out(d.current_url))
        if is_logged_in_LN(driver):
            print_lg("Login successful!")
            return True
        print_lg("Login page left, but logged-in verification failed.")
        return False
    except Exception as e:
        print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
        manual_login_retry(lambda: is_logged_in_LN(driver), 2)
        return is_logged_in_LN(driver)

def manual_login_retry(is_logged_in_func, limit=2):
    count = 0
    while not is_logged_in_func():
        print_lg("Seems like you're not logged in!")
        button = "Confirm Login"
        message = 'After you successfully Log In, please click "{}" button below.'.format(button)
        if count > limit:
            button = "Skip Confirmation"
            message = 'If you\'re seeing this message even after you logged in, Click "{}". Seems like auto login confirmation failed!'.format(button)
        count += 1
        if pyautogui.alert(message, "Login Required", button) and count > limit: return
