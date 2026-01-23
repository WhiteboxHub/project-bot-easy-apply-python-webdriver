from selenium.webdriver.common.by import By

# Enhanced selector registry with fallback support
# Each selector can have a primary and optional fallback locator

LOCATORS = {
    "next": {
        "primary": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
        "fallback": (By.XPATH, "//button[contains(text(), 'Next') or contains(text(), 'Continue')]")
    },
    
    "review": {
        "primary": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
        "fallback": (By.XPATH, "//button[contains(text(), 'Review')]")
    },
    
    "submit": {
        "primary": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
        "fallback": (By.XPATH, "//button[contains(text(), 'Submit')]")
    },
    
    "error": {
        "primary": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
        "fallback": (By.CSS_SELECTOR, ".artdeco-inline-feedback")
    },
    
    "upload_resume": {
        "primary": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
        "fallback": (By.CSS_SELECTOR, "input[type='file'][id*='resume']")
    },
    
    "upload_cv": {
        "primary": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
        "fallback": (By.CSS_SELECTOR, "input[type='file'][id*='cover']")
    },
    
    "follow": {
        "primary": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
        "fallback": (By.XPATH, "//label[contains(text(), 'Follow')]")
    },
    
    "upload": {
        "primary": (By.NAME, "file"),
        "fallback": (By.CSS_SELECTOR, "input[type='file']")
    },
    
    "search": {
        "primary": (By.CLASS_NAME, "jobs-search-results-list"),
        "fallback": (By.CSS_SELECTOR, ".jobs-search-results__list")
    },
    
    "links": {
        "primary": ("xpath", '//div[@data-job-id]'),
        "fallback": ("css", "div.job-card-container")
    },
    
    "fields": {
        "primary": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
        "fallback": (By.CSS_SELECTOR, ".jobs-easy-apply-form-element")
    },
    
    "radio_select": {
        "primary": (By.CSS_SELECTOR, "input[type='radio']"),
        "fallback": (By.XPATH, "//input[@type='radio']")
    },
    
    "multi_select": {
        "primary": (By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]"),
        "fallback": (By.CSS_SELECTOR, "[id*='text-entity-list']")
    },
    
    "text_select": {
        "primary": (By.CLASS_NAME, "artdeco-text-input--input"),
        "fallback": (By.CSS_SELECTOR, "input[type='text']")
    },
    
    "2fa_oneClick": {
        "primary": (By.ID, 'reset-password-submit-button'),
        "fallback": (By.CSS_SELECTOR, "button[type='submit']")
    },
    
    "easy_apply_button": {
        "primary": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]'),
        "fallback": (By.CSS_SELECTOR, "button[aria-label*='Easy Apply']")
    }
}


def get_locator(key: str, use_fallback: bool = False):
    """
    Get a locator by key, optionally returning the fallback.
    
    Args:
        key: The selector key
        use_fallback: If True, return fallback locator if available
    
    Returns:
        Tuple of (By, selector) or the original value if not dict
    """
    locator = LOCATORS.get(key)
    
    if not locator:
        return None
    
    # If it's a dict with primary/fallback
    if isinstance(locator, dict):
        if use_fallback and "fallback" in locator:
            return locator["fallback"]
        return locator.get("primary", locator.get("fallback"))
    
    # Legacy format (direct tuple)
    return locator


def has_fallback(key: str) -> bool:
    """Check if a selector has a fallback defined"""
    locator = LOCATORS.get(key)
    return isinstance(locator, dict) and "fallback" in locator
