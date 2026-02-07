import os
from time import sleep
from random import randint
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException

from bot.utils.delays import buffer
from bot.utils.logger import print_lg, log_step
from bot.utils.retry import retry
from bot.utils.shadow_dom import find_and_click_robust, find_in_shadow_root, robust_click, is_element_visible
from bot.utils.selectors import Selectors, SelectorRegistry
from bot.persistence.qa_manager import QAManager
import pyautogui

# Global QAManager instance
qa_store = QAManager()

def get_setting(name, default):
    """Try to get a setting from __main__ or use default."""
    import __main__
    return getattr(__main__, name, default)

def scroll_to_view(driver: WebDriver, element: WebElement, top: bool = False, smooth_scroll: bool = None) -> None:
    if smooth_scroll is None:
        smooth_scroll = get_setting("smooth_scroll", False)
    if top:
        return driver.execute_script('arguments[0].scrollIntoView();', element)
    behavior = "smooth" if smooth_scroll else "instant"
    return driver.execute_script(f'arguments[0].scrollIntoView({{block: "center", behavior: "{behavior}" }});', element)

@retry(max_attempts=3, delay=1, exceptions=(Exception, StaleElementReferenceException))
def wait_span_click(driver: WebDriver, text: str, time: float=5.0, click: bool=True, scroll: bool=True, scrollTop: bool=False) -> WebElement | bool:
    if not text: return False
    log_step("wait_span_click", "Attempting", details=f"Target: {text}")
    try:
        registry_selectors = SelectorRegistry.get(text)
        button = None
        wait_context = driver
        real_driver = driver if hasattr(driver, "execute_script") else getattr(driver, "parent", driver)
        
        if registry_selectors:
            for strategy, selector in registry_selectors:
                try:
                    if strategy == "XPATH":
                        button = WebDriverWait(wait_context, time/len(registry_selectors)).until(EC.element_to_be_clickable((By.XPATH, selector)))
                    elif strategy == "CSS":
                        button = WebDriverWait(wait_context, time/len(registry_selectors)).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    if button: break
                except: continue
        else:
            xpath = f'.//span[contains(translate(normalize-space(.), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{text.lower()}")]'
            button = WebDriverWait(wait_context, time).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        
        if not button: return False
        if scroll: scroll_to_view(real_driver, button, scrollTop)
        if click:
            try: button.click()
            except: real_driver.execute_script("arguments[0].click();", button)
            buffer(get_setting("click_gap", 2))
        return button
    except Exception as e:
        raise

def try_xp(driver: WebDriver, xpath: str, click: bool=True) -> WebElement | bool:
    try:
        if click:
            driver.find_element(By.XPATH, xpath).click()
            return True
        else:
            return driver.find_element(By.XPATH, xpath)
    except: return False

def try_linkText(driver: WebDriver, linkText: str) -> WebElement | bool:
    try: return driver.find_element(By.LINK_TEXT, linkText)
    except: return False

def find_by_class(driver: WebDriver, class_name: str, time: float=5.0) -> WebElement:
    return WebDriverWait(driver, time).until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))

def text_input_by_ID(driver: WebDriver, id: str, value: str, time: float=5.0) -> None:
    field = WebDriverWait(driver, time).until(EC.presence_of_element_located((By.ID, id)))
    field.send_keys(Keys.CONTROL + "a")
    field.send_keys(value)

def text_input(actions: ActionChains, textInputEle: WebElement | bool, value: str, textFieldName: str = "Text") -> None:
    if textInputEle:
        textInputEle.clear()
        textInputEle.send_keys(value.strip())
        sleep(1)
        actions.send_keys(Keys.ENTER).perform()

import yaml
from pathlib import Path

# Load Dynamic Configuration
FORM_CONFIG_PATH = Path("bot/config/form_filling.yaml")
if FORM_CONFIG_PATH.exists():
    with open(FORM_CONFIG_PATH, "r") as f:
        FORM_CONFIG = yaml.safe_load(f)
else:
    FORM_CONFIG = {}

def get_mapping(category: str) -> dict:
    return FORM_CONFIG.get(category, {})

def is_field_required(Question: WebElement) -> bool:
    """Check if the field is marked as required by LinkedIn using dynamic indicators."""
    try:
        req_cfg = FORM_CONFIG.get("required_indicators", {})
        
        # Check text indicators (*, Required, etc)
        for txt in req_cfg.get("text", ["*"]):
            if Question.find_elements(By.XPATH, f".//*[contains(text(), '{txt}')]"):
                return True
        
        # Check class indicators
        for cls in req_cfg.get("classes", []):
            if Question.find_elements(By.XPATH, f".//*[contains(@class, '{cls}')]"):
                return True
        
        # Check attribute indicators
        inputs = Question.find_elements(By.XPATH, ".//input | .//select | .//textarea")
        for inp in inputs:
            for attr in req_cfg.get("attributes", []):
                if inp.get_attribute(attr) in ["true", "required", attr]:
                    return True
    except: pass
    return False

def answer_common_questions(label: str, vars: dict) -> str:
    """
    Smarter heuristic using dynamic logic mappings from YAML.
    """
    label = label.lower()
    
    # 1. Constant Mappings (e.g., "Degree" -> "Yes")
    const_map = FORM_CONFIG.get("constant_mappings", {})
    for answer, keywords in const_map.items():
        if any(k.lower() in label for k in keywords):
            return answer

    # 2. Variable Mappings (Label Keyword -> Candidate Variable)
    # Priority: Longest keyword match first to avoid partial match bugs (e.g. 'salary' vs 'experience')
    logic_map = FORM_CONFIG.get("logic_mappings", {})
    all_keywords = []
    for var_name, keywords in logic_map.items():
        for k in keywords:
            all_keywords.append((k.lower(), var_name))
    
    all_keywords.sort(key=lambda x: len(x[0]), reverse=True)

    for keyword, var_name in all_keywords:
        if keyword in label:
            val = vars.get(var_name, "")
            # Special logic for citizenship strings
            if var_name == "us_citizenship" and str(val).lower() == "yes":
                return "Yes"
            if var_name == "us_citizenship" and str(val).lower() == "no":
                return "No"
            return str(val)

    return '' 

def _click_radio_option(question_ele: WebElement, radio: WebElement) -> bool:
    """Robust radio selection: input click -> JS click -> label click, then verify selected."""
    try:
        radio.click()
    except Exception:
        try:
            question_ele.parent.execute_script("arguments[0].click();", radio)
        except Exception:
            pass

    try:
        if radio.is_selected():
            return True
    except Exception:
        pass

    try:
        radio_id = radio.get_attribute("id")
        if radio_id:
            label_ele = question_ele.find_element(By.XPATH, f".//label[@for=\"{radio_id}\"]")
            try:
                label_ele.click()
            except Exception:
                question_ele.parent.execute_script("arguments[0].click();", label_ele)
            sleep(0.2)
            return radio.is_selected()
    except Exception:
        pass

    return False

def answer_questions(modal: WebElement, questions_list: set, vars: dict, job_description: str | None = None) -> set:
    all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")
    id_map = FORM_CONFIG.get("identity_mappings", {})

    for Question in all_questions:
        required = is_field_required(Question)
        
        # 1. Select / Dropdown
        select_ele = try_xp(Question, ".//select", False)
        if select_ele:
            try:
                label_org = Question.find_element(By.TAG_NAME, "label").find_element(By.TAG_NAME, "span").text
                label = label_org.lower()
                
                stored_answer = qa_store.find_answer(label_org)
                select = Select(select_ele)
                
                if stored_answer:
                    try: 
                        select.select_by_visible_text(stored_answer)
                        questions_list.add((label_org, stored_answer, "select (stored)"))
                        continue
                    except: pass

                if vars.get('overwrite_previous_answers', False) or select.first_selected_option.text == "Select an option":
                    answer = answer_common_questions(label, vars)
                    try: 
                        if answer:
                            select.select_by_visible_text(answer)
                            questions_list.add((label_org, answer, "select"))
                        else: raise Exception("No answer")
                    except: 
                        if required and vars.get('manual_mode', True):
                            pyautogui.alert(f"Required Dropdown needs attention:\n\n{label_org}\n\nPlease select the value in the browser and click OK.", "Manual Action Required")
                            questions_list.add((label_org, "Manual", "select (manual)"))
                        else:
                            if len(select.options) > 1: 
                                select.select_by_index(randint(1, len(select.options)-1))
                                questions_list.add((label_org, select.first_selected_option.text, "select (random)"))
            except: pass
            continue

        # 2. Radio Group
        radio_group = Question.find_elements(By.XPATH, ".//input[@type='radio']")
        if radio_group:
            try:
                label_ele = try_xp(Question, ".//span[@data-test-form-builder-radio-button-group__label]/span[1] | .//legend//span[1]", False)
                label_org = label_ele.text if label_ele else "unknown"
                label = label_org.lower()
                
                stored_answer = qa_store.find_answer(label_org)
                if stored_answer:
                    for radio in radio_group:
                        opt_text = radio.find_element(By.XPATH, "./following-sibling::label").text.lower()
                        if stored_answer.lower() in opt_text:
                            if _click_radio_option(Question, radio):
                                questions_list.add((label_org, stored_answer, "radio (stored)"))
                                break
                    if any(q[0] == label_org and "radio" in q[2] for q in questions_list):
                        continue

                answer = answer_common_questions(label, vars)
                log_step("Form Filling", "Answering Radio", details=f"{label} -> {answer}")
                found_radio = False
                if answer:
                    for radio in radio_group:
                        opt_text = radio.find_element(By.XPATH, "./following-sibling::label").text.lower()
                        if answer.lower() in opt_text:
                            found_radio = _click_radio_option(Question, radio)
                            if found_radio:
                                questions_list.add((label_org, answer, "radio"))
                                break
                
                if not found_radio:
                    if required and vars.get('manual_mode', True):
                        pyautogui.alert(f"Required Radio Question needs attention:\n\n{label_org}\n\nPlease pick an option in the browser and click OK.", "Manual Action Required")
                        questions_list.add((label_org, "Manual", "radio (manual)"))
                    else:
                        log_step("Form Filling", "Warning", details=f"Radio question unresolved: {label_org}")
            except: pass
            continue

        # 3. Text Inputs
        text_ele = try_xp(Question, ".//input[not(@type='radio' or @type='checkbox' or @type='submit' or @type='file')]", False)
        if text_ele:
            try:
                label_org = Question.find_element(By.TAG_NAME, "label").text
                label = label_org.lower()
                
                log_step("Form Filling", "Processing Label", details=label_org)

                current_val = text_ele.get_attribute("value")
                if current_val and not vars.get('overwrite_previous_answers', False):
                    questions_list.add((label_org, current_val, "input (skipped)"))
                    continue

                stored_answer = qa_store.find_answer(label_org)
                if stored_answer:
                    text_ele.clear()
                    text_ele.send_keys(stored_answer)
                    questions_list.add((label_org, stored_answer, "input (stored)"))
                    continue

                answer = ""
                matched = False
                
                # 1. Identity Mappings (Dynamic)
                for var_name, keywords in id_map.items():
                    if any(k.lower() in label for k in keywords):
                        answer = str(vars.get(var_name, ""))
                        matched = True
                        break
                
                # 2. Logic Mappings (Dynamic)
                if not matched:
                    answer = answer_common_questions(label, vars)
                    if answer: matched = True

                # 3. Numeric fallback (Generic)
                if not matched and any(num_word in label for num_word in ["how many", "years", "number", "level"]):
                    answer = "0"
                    matched = True

                if matched and answer:
                    text_ele.clear()
                    text_ele.send_keys(answer)
                    questions_list.add((label_org, answer, "input"))
                else:
                    if required and vars.get('manual_mode', True):
                        pyautogui.alert(f"Required Field needs attention:\n\n{label_org}\n\nPlease enter the answer in the browser and click OK.", "Manual Action Required")
                        questions_list.add((label_org, "Manual", "input (manual)"))
                    else:
                        questions_list.add((label_org, "Skipped", "input (skipped)"))
            except: pass
            continue
    return questions_list

def upload_resume(modal, resume_path):
    try:
        if not os.path.exists(resume_path): return False, "Missing"
        file_input = modal.find_element(By.XPATH, ".//input[@type='file']")
        file_input.send_keys(os.path.abspath(resume_path))
        return True, resume_path
    except: return False, "Failed"
