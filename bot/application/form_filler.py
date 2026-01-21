import time
import logging
from selenium.webdriver.common.by import By.
from bot.persistence.store import Store
from bot.utils.selectors import LOCATORS
from bot.utils.logger import logger


class FormFiller:
    def __init__(self, browser, salary="100000"):
        self.browser = browser
        self.salary = salary
        self.store = Store()
        self.locator = LOCATORS

    def fill_out_fields(self, phone_number):
        fields = self.browser.find_elements(By.CLASS_NAME, "jobs-easy-apply-form-section__grouping")
        for field in fields:
            if "Mobile phone number" in field.text:
                field_input = field.find_element(By.TAG_NAME, "input")
                field_input.clear()
                field_input.send_keys(phone_number)

    def process_questions(self):
        time.sleep(1)
        form = self.get_elements("fields")
        for field in form:
            question = field.text
            answer = self.ans_question(question.lower())

            if self.is_present(self.locator["radio_select"]):
                try:
                    input = field.find_element(By.CSS_SELECTOR, "input[type='radio'][value={}]".format(answer))
                    self.browser.execute_script("arguments[0].click();", input)
                except Exception as e:
                    # log.error(e)
                    pass

            elif self.is_present(self.locator["multi_select"]):
                try:
                    input = field.find_element(By.XPATH, "//*[contains(@id, 'text-entity-list-form-component')]")
                    input.send_keys(answer)
                except Exception as e:
                    pass

            elif self.is_present(self.locator["text_select"]):
                try:
                    input = field.find_element(By.CLASS_NAME, "artdeco-text-input--input")
                    input.send_keys(answer)
                except Exception as e:
                    pass

            # Fallback for Yes/No radio if structure differs
            if "Yes" in str(answer) or "No" in str(answer):
                try:
                    input = field.find_element(By.CSS_SELECTOR, "input[type='radio'][value={}]".format(answer))
                    self.browser.execute_script("arguments[0].click();", input)
                except:
                    pass
            else:
                 try:
                    input = field.find_element(By.CLASS_NAME, "artdeco-text-input--input")
                    input.send_keys(answer)
                 except:
                    pass
    
    def ans_question(self, question):
        # Check store first
        stored_answer = self.store.get_answer(question)
        if stored_answer:
            return stored_answer

        answer = None
        if "how many" in question:
            answer = "1"
        elif "experience" in question:
            answer = "1"
        elif "sponsor" in question:
            answer = "No"
        elif 'do you ' in question:
            answer = "Yes"
        elif "have you " in question:
            answer = "Yes"
        elif "US citizen" in question:
            answer = "Yes"
        elif "are you " in question:
            answer = "Yes"
        elif "salary" in question:
            answer = self.salary
        elif "can you" in question:
            answer = "Yes"
        elif "gender" in question:
            answer = "Male"
        elif "race" in question:
            answer = "Wish not to answer"
        elif "lgbtq" in question:
            answer = "Wish not to answer"
        elif "ethnicity" in question:
            answer = "Wish not to answer"
        elif "nationality" in question:
            answer = "Wish not to answer"
        elif "government" in question:
            answer = "I do not wish to self-identify"
        elif "are you legally" in question:
            answer = "Yes"
        else:
            logger.info("Not able to answer question automatically. Please provide answer", step="ans_question", event="manual_required")
            answer = "user provided"
            # time.sleep(15) # Maybe prompt or wait?
        
        logger.info("Answering question: " + question + " with answer: " + answer, step="ans_question", event="answered")
        self.store.save_answer(question, answer)
        return answer


    def get_elements(self, type) -> list:
        elements = []
        element = self.locator[type]
        if self.is_present(element):
            elements = self.browser.find_elements(element[0], element[1])
        return elements

    def is_present(self, locator):
        if isinstance(locator, list):
             locator = tuple(locator)
        return len(self.browser.find_elements(locator[0], locator[1])) > 0
