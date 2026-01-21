from selenium.webdriver.common.by import By

LOCATORS = {
    "next": (By.CSS_SELECTOR, "button[aria-label='Continue to next step']"),
    "review": (By.CSS_SELECTOR, "button[aria-label='Review your application']"),
    "submit": (By.CSS_SELECTOR, "button[aria-label='Submit application']"),
    "error": (By.CLASS_NAME, "artdeco-inline-feedback__message"),
    "upload_resume": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]"),
    "upload_cv": (By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]"),
    "follow": (By.CSS_SELECTOR, "label[for='follow-company-checkbox']"),
    "upload": (By.NAME, "file"),
    "search": (By.CLASS_NAME, "jobs-search-results-list"),
    "links": ("xpath", '//div[@data-job-id]'),
    "fields": (By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"),
    "radio_select": (By.CSS_SELECTOR, "input[type='radio']"), 
    "multi_select": (By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]"),
    "text_select": (By.CLASS_NAME, "artdeco-text-input--input"),
    "2fa_oneClick": (By.ID, 'reset-password-submit-button'),
    "easy_apply_button": (By.XPATH, '//button[contains(@class, "jobs-apply-button")]')
}
