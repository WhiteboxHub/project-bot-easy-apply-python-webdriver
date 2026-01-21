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
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    def is_present(self, locator):
        return len(self.browser.find_elements(locator[0], locator[1])) > 0

    @retry(max_attempts=5, delay=1)
    def send_resume(self, jobID=None) -> bool:
        def is_present(button_locator) -> bool:


            return len(self.browser.find_elements(button_locator[0], button_locator[1])) > 0

        try:
            submitted = False
            loop = 0
            while loop < 2:
                time.sleep(1)
                # Upload resume
                if is_present(self.locator["upload_resume"]):
                    try:
                        resume_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-resume')]")
                        resume = self.uploads.get("Resume")
                        if resume:
                            resume_locator.send_keys(resume)
                    except Exception as e:
                        logger.error(f"Resume upload failed: {e}", job_id=jobID, step="upload_resume", exception=e)

                # Upload cover letter

                if is_present(self.locator["upload_cv"]):
                    cv = self.uploads.get("Cover Letter")
                    if cv:
                        try:
                            cv_locator = self.browser.find_element(By.XPATH, "//*[contains(@id, 'jobs-document-upload-file-input-upload-cover-letter')]")
                            cv_locator.send_keys(cv)
                        except Exception as e:
                             pass

                elif len(self.get_elements("follow")) > 0:
                    elements = self.get_elements("follow")
                    for element in elements:
                        try:
                             button = self.wait.until(EC.element_to_be_clickable(element))
                             self.human.click(button)
                        except: pass

                if len(self.get_elements("submit")) > 0:

                    elements = self.get_elements("submit")
                    for element in elements:
                        button = self.wait.until(EC.element_to_be_clickable(element))
                        
                        if self.dry_run and not self.dry_run.validate_submit():
                             submitted = True # Pretend success for workflow continuity
                             logger.info("Fake success for dry run", job_id=jobID, step="submit", event="dry_run_success")
                             break
                        
                        self.human.click(button)
                        logger.info("Application Submitted", job_id=jobID, step="submit", event="success")
                        submitted = True
                        if self.metrics: self.metrics.increment("submitted")

                        break




                elif len(self.get_elements("error")) > 0:
                    elements = self.get_elements("error")
                    if "application was sent" in self.browser.page_source:
                        logger.info("Application Submitted", job_id=jobID, step="submit", event="success_after_check")
                        submitted = True
                        break
                    elif len(elements) > 0:
                        while len(elements) > 0:
                            logger.info("Please answer the questions, waiting 5 seconds...", job_id=jobID, step="questions")
                            time.sleep(5)

                            elements = self.get_elements("error")
                            for element in elements:
                                self.form_filler.process_questions()

                            if "application was sent" in self.browser.page_source:
                                logger.info("Application Submitted", job_id=jobID, step="submit", event="success_after_questions")
                                submitted = True
                                break
                            elif is_present(self.locator["easy_apply_button"]):
                                logger.info("Skipping application", job_id=jobID, step="process", event="skip")
                                if self.metrics: self.metrics.increment("skipped")
                                submitted = False
                                break

                        continue

                    else:
                        logger.info("Application not submitted", job_id=jobID, step="submit", event="failed")
                        if self.metrics: self.metrics.increment("failed")
                        time.sleep(2)
                        break



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


