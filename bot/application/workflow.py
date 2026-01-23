import os
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bot.application.form_filler import FormFiller
from bot.persistence.store import Store
from bot.utils.selectors import LOCATORS
from bot.utils.logger import logger
from bot.utils.retry import retry
from bot.utils.human_interaction import HumanInteraction




class Workflow:
    def __init__(self, browser, uploads, blacklist_titles=None, execution_guard=None, dry_run=None, metrics=None):
        self.browser = browser.driver
        self.wait = WebDriverWait(self.browser, 30)

        self.uploads = uploads
        self.blacklist_titles = blacklist_titles or []
        self.store = Store()
        self.form_filler = FormFiller(self.browser)
        self.locator = LOCATORS
        self.execution_guard = execution_guard
        self.dry_run = dry_run
        self.human = HumanInteraction(self.browser)
        self.metrics = metrics

    def apply_to_job(self, jobID, phone_number):
        if self.metrics:
            self.metrics.increment("attempted")

        if self.execution_guard and not self.execution_guard.can_apply():
             if self.metrics: self.metrics.increment("skipped")
             return False


        self.get_job_page(jobID)

        time.sleep(1)

        button = self.get_easy_apply_button()

        if button is not False:
            if any(word in self.browser.title for word in self.blacklist_titles):
                logger.info('skipping this application, a blacklisted keyword was found in the job position', job_id=jobID, step="apply", event="blacklist")
                string_easy = "* Contains blacklisted keyword"
                result = False
            else:
                string_easy = "* has Easy Apply Button"
                logger.info("Clicking the EASY apply button", job_id=jobID, step="apply", event="click_apply")
                self.human.click(button)
                time.sleep(1)
                self.form_filler.fill_out_fields(phone_number)

                result = self.send_resume(jobID)

                if result:
                    string_easy = "*Applied: Sent Resume"
                else:
                    string_easy = "*Did not apply: Failed to send Resume"
        elif "You applied on" in self.browser.page_source:
            logger.info("You have already applied to this position.", job_id=jobID, step="apply", event="already_applied")
            string_easy = "* Already Applied"
            result = False
        else:
            logger.info("The Easy apply button does not exist.", job_id=jobID, step="apply", event="no_button")
            string_easy = "* Doesn't have Easy Apply Button"
            result = False

        logger.info(f"\nPosition {jobID}:\n {self.browser.title} \n {string_easy} \n", job_id=jobID, step="apply", event="summary")

        self.store.write_to_file(button, jobID, self.browser.title, result)
        return result

    @retry(max_attempts=3, delay=1)
    def get_job_page(self, jobID):
        job = 'https://www.linkedin.com/jobs/view/' + str(jobID)
        self.browser.get(job)
        # self.load_page(sleep=0.5) # logic handled elsewhere?

    @retry(max_attempts=3, delay=1)
    def get_easy_apply_button(self):
        EasyApplyButton = False
        try:
            buttons = self.get_elements("easy_apply_button")
            for button in buttons:
                if "Easy Apply" in button.text:
                    EasyApplyButton = button
                    self.wait.until(EC.element_to_be_clickable(EasyApplyButton))
                else:
                    logger.debug("Easy Apply button not found", step="get_button")
        except Exception as e:
            if self.metrics: self.metrics.increment("failed")
            logger.debug(f"Easy Apply button not found: {e}", step="get_button", exception=e)
        return EasyApplyButton




    def get_elements(self, type) -> list:
        elements = []
        element = self.locator[type]
        
        if isinstance(element, dict):
            element = element.get('primary', element.get('fallback'))
            
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    def is_present(self, locator):
        if isinstance(locator, dict):
            locator = locator.get('primary', locator.get('fallback'))
            
        return len(self.browser.find_elements(locator[0], locator[1])) > 0

    @retry(max_attempts=5, delay=1)
    def send_resume(self, jobID=None) -> bool:
        def is_present(button_locator) -> bool:
            if isinstance(button_locator, dict):
                button_locator = button_locator.get('primary', button_locator.get('fallback'))

            return len(self.browser.find_elements(button_locator[0], button_locator[1])) > 0

        try:
            submitted = False
            loop = 0
            while loop < 20: # Increased loop limit for multi-page forms
                time.sleep(1)
                # Upload resume
                if is_present(self.locator["upload_resume"]):
                    try:
                        resume_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]")
                        resume = self.uploads.get("Resume")
                        if resume:
                            abs_resume = os.path.abspath(resume)
                            resume_locator.send_keys(abs_resume)
                            logger.info(f"Uploaded resume: {abs_resume}", job_id=jobID, step="upload_resume")
                    except Exception as e:
                        logger.error(f"Resume upload failed: {e}", job_id=jobID, step="upload_resume", exception=e)

                # Upload cover letter
                # Upload cover letter
                if is_present(self.locator["upload_cv"]):
                    cv = self.uploads.get("Cover Letter")
                    if cv:
                        try:
                            cv_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]")
                            abs_cv = os.path.abspath(cv)
                            cv_locator.send_keys(abs_cv)
                            logger.info(f"Uploaded cover letter: {abs_cv}", job_id=jobID, step="upload_cv")
                        except Exception as e:
                             pass

                # NEW: Click 'Follow Company' if requested and present
                follow_elements = self.get_elements("follow")
                if follow_elements:
                    for element in follow_elements:
                        try:
                            # Only click if it's not already checked (often it's a label for a checkbox)
                            self.browser.execute_script("arguments[0].click();", element)
                            logger.info("Clicked 'Follow Company' checkbox", job_id=jobID, step="follow")
                        except: pass

                if len(self.get_elements("submit")) > 0:
                    elements = self.get_elements("submit")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        
                        if self.dry_run and not self.dry_run.validate_submit():
                             submitted = True 
                             logger.info("Fake success for dry run", job_id=jobID, step="submit", event="dry_run_success")
                             break
                        
                        self.human.click(button)
                        logger.info("Application Submitted", job_id=jobID, step="submit", event="success")
                        submitted = True
                        if self.metrics: self.metrics.increment("submitted")
                        break
                    
                    if submitted: break # Exit the WHILE loop immediately

                elif len(self.get_elements("error")) > 0:
                    logger.warning("⚠️ Form contains errors or missing required fields.", job_id=jobID, step="form_error")
                    
                    # Try to solve automatically first (one attempt)
                    logger.info("Attempting to auto-solve questions...", job_id=jobID, step="auto_solve")
                    elements = self.get_elements("error")
                    for element in elements:
                        self.form_filler.process_questions()
                    
                    time.sleep(2)
                    
                    # Check if errors still exist
                    elements = self.get_elements("error")
                    if len(elements) > 0:
                        logger.info("🛑 PAUSED: Bot cannot solve these questions. PLEASE SOLVE THEM MANUALLY.", job_id=jobID, step="manual_intervention")
                        logger.info("⏰ I will wait indefinitely until you clear the errors. You can take as much time as you need.", job_id=jobID, step="waiting")
                        
                        # Wait forever until errors are cleared
                        while len(self.get_elements("error")) > 0:
                            time.sleep(5) # Just sit and wait
                            # Check if the job was closed or we navigated away
                            if "You applied on" in self.browser.page_source or "application was sent" in self.browser.page_source:
                                break
                            if is_present(self.locator["easy_apply_button"]):
                                break
                        
                        logger.info("✅ Errors cleared! Resuming...", job_id=jobID, step="resuming")
                    
                    continue # Try the page again (to click Next or Submit)


                elif len(self.get_elements("next")) > 0:
                    elements = self.get_elements("next")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.human.click(button)

                elif len(self.get_elements("review")) > 0:
                    elements = self.get_elements("review")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.human.click(button)

                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        self.human.click(button)
                
                loop += 1 # Avoid infinite loop if stuck


        except Exception as e:
            logger.error(f"Cannot apply to this job: {e}", job_id=jobID, step="apply_loop", exception=e)
            if self.metrics: self.metrics.increment("failed")
            pass

        if submitted and self.execution_guard:

             self.execution_guard.on_success()

        return submitted


