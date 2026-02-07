import os
import pyautogui
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

from bot.application.form_filler import (
    wait_span_click, find_by_class, answer_questions, 
    upload_resume, try_xp, FORM_CONFIG
)
from bot.core.dry_run import discard_application
from bot.discovery.job_identity import get_job_main_details, calculate_date_posted
from bot.discovery.job_identity import extract_years_of_experience
from bot.utils.logger import print_lg
from bot.utils.delays import buffer
from bot.core.metrics import update_candidate_count
from bot.utils.selectors import Selectors, SelectorRegistry


def _modal_has_validation_error(modal) -> tuple[bool, str]:
    """Detect common LinkedIn Easy Apply validation errors using dynamic selectors."""
    try:
        err_selectors = SelectorRegistry.get("validation_errors")
        for strategy, selector in err_selectors:
            if strategy == "XPATH":
                elements = modal.find_elements(By.XPATH, selector)
                for e in elements:
                    txt = (e.text or "").strip()
                    if txt: return True, txt
    except Exception:
        pass
    return False, ""

def process_job_application(driver, actions, wait, job_id, title, company, vars, db, counts_data):
    """
    High-level workflow for applying to a single job.
    Returns True if successfully applied.
    """
    print_lg(f"Applying to: {title} at {company} (ID: {job_id})")
    
    try:
        # 1. Click Easy Apply
        if not wait_span_click(driver, "apply_button", 5):
            print_lg(f"Easy Apply button not found for {title}")
            return False

        # Use configurable delay from YAML
        spawn_delay = FORM_CONFIG.get("settings", {}).get("modal_spawn_delay", 4)
        buffer(spawn_delay) 

        # 2. Modal Loop
        questions_list = set()
        next_button = True
        
        step_count = 0
        max_steps = int(vars.get('max_modal_steps', 12) or 12)

        while next_button:
            step_count += 1
            if step_count > max_steps:
                print_lg(f"❌ Modal step limit exceeded ({max_steps}) for {title}. Stopping to avoid infinite loop.")
                discard_application(driver, actions)
                return False

            # RE-FIND MODAL
            try:
                # Increased timeout to 10s for stability
                modal = find_by_class(driver, Selectors.MODAL_CONTAINER, time=10)
            except:
                print_lg("Modal not found (Timeout). LinkedIn may be slow or the button didn't trigger it.")
                return False

            # Answer questions on current page
            answer_questions(modal, questions_list, vars)

            # Detect unresolved validation state
            has_error, err_text = _modal_has_validation_error(modal)
            if has_error:
                print_lg(f"⚠️ Validation error in form: {err_text}")
                if vars.get('manual_mode', True) or vars.get('pause_at_failed_question', True):
                    pyautogui.alert(
                        f"Manual action required for application form.\n\nJob: {title}\nIssue: {err_text}\n\nPlease fix the field and click OK to continue.",
                        "LinkedIn Easy Apply - Validation Error",
                        "OK"
                    )
                    # Re-find modal after pause
                    try: modal = find_by_class(driver, Selectors.MODAL_CONTAINER, time=2)
                    except: return False
            
            # Try to navigate forward
            if wait_span_click(modal, "modal_review", 1):
                print_lg("Review page reached.")
                next_button = False
            elif wait_span_click(modal, "modal_next", 2):
                print_lg("Moving to next step.")
            else:
                if vars.get('manual_mode', True):
                    choice = pyautogui.confirm(
                        "I can't find the 'Next' or 'Review' button. Are you still working on this step?\n\n(Click 'Continue' after you fix it manually, or 'Discard' to skip)",
                        "Manual Intervention",
                        ["Continue", "Discard Application"]
                    )
                    if choice == "Discard Application":
                        discard_application(driver, actions)
                        return False
                else:
                    print_lg("No Next/Review button found. Possibly stuck or at end.")
                    next_button = False

        # 3. Final Submission
        if vars.get('dry_run'):
            print_lg(f"🧪 [DRY RUN] Skipping submission for {title}")
            discard_application(driver, actions)
            return True 
        
        if vars.get('manual_mode', True):
            decision = pyautogui.confirm(
                f'1. Please verify your information for: {title}\n\nReady to submit?', 
                "Confirm your information",
                ["Discard Application", "Submit Application"]
            )
            if decision == "Discard Application":
                discard_application(driver, actions)
                return False

        if wait_span_click(driver, "modal_submit", 5, scrollTop=True):
            print_lg(f"✅ Successfully applied to {title}!")
            wait_span_click(driver, "modal_done", 3)
            return True
        else:
            if vars.get('manual_mode', True):
                if "Yes" in pyautogui.confirm(
                    "You submitted the application, didn't you 😒?", 
                    "Failed to find Submit Application!", 
                    ["Yes", "No"]
                ):
                    print_lg(f"✅ User confirmed manual submission for {title}.")
                    return True

            print_lg(f"❌ Failed to find Submit button for {title}")
            discard_application(driver, actions)
            return False

    except Exception as e:
        print_lg(f"Error applying to job {job_id}: {e}")
        discard_application(driver, actions)
        return False

def get_job_description(driver, vars) -> tuple:
    """
    Extracts job description and checks against criteria from YAML.
    """
    bad_words = vars.get('bad_words', [])
    security_clearance = vars.get('security_clearance', False)
    did_masters = vars.get('did_masters', False)
    current_experience = vars.get('current_experience', 0)
    
    screening_cfg = FORM_CONFIG.get("screening", {})
    clearance_words = screening_cfg.get("clearance_keywords", ['polygraph', 'clearance', 'secret'])
    
    try:
        job_desc_ele = find_by_class(driver, "jobs-box__html-content")
        description = job_desc_ele.text
        description_low = description.lower()
        
        # Bad words check
        for word in bad_words:
            if word.lower() in description_low:
                return description, "Unknown", True, "Bad Word", f"Found bad word: {word}"
        
        # Clearance check
        if not security_clearance and any(w in description_low for w in clearance_words):
            return description, "Unknown", True, "Clearance", "Requires security clearance"
            
        # Experience check
        exp_req = extract_years_of_experience(description)
        found_masters = 2 if did_masters and 'master' in description_low else 0
        leniency = int(vars.get('experience_leniency', 3))
        if current_experience > -1 and exp_req > (int(current_experience) + found_masters + leniency):
            return description, exp_req, True, "Experience", f"Requires {exp_req} years (Leniency allowed: {int(current_experience) + found_masters + leniency})"
            
        return description, exp_req, False, None, None
    except Exception as e:
        return "Unknown", "Unknown", False, "Error", str(e)
