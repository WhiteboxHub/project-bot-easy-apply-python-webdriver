import re
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from bot.application.form_filler import scroll_to_view
from bot.utils.delays import buffer
from bot.utils.selectors import Selectors, SelectorRegistry

re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\s*\d*[+]*\s*year[s]?', re.IGNORECASE)

def get_job_main_details(driver, job: WebElement, blacklisted_companies: set, rejected_jobs: set) -> tuple[str, str, str, str, str, bool]:
    '''
    Extracts job basic info from the card using dynamic selectors.
    '''
    try:
        job_details_button = job.find_element(By.TAG_NAME, 'a')
        scroll_to_view(driver, job_details_button, True)
        
        job_id = job.get_dom_attribute('data-occludable-job-id')
        title = job_details_button.text.split("\n")[0]
        
        # Use dynamic Selector for subtitle
        sub_selectors = SelectorRegistry.get("job_card_subtitle")
        other_details = "Unknown"
        for strategy, selector in sub_selectors:
            try:
                if strategy == "CLASS":
                    other_details = job.find_element(By.CLASS_NAME, selector).text
                elif strategy == "XPATH":
                    other_details = job.find_element(By.XPATH, selector).text
                break
            except: continue

        sep = Selectors.JOB_CARD_SEPARATOR or " · "
        index = other_details.find(sep)
        company = other_details[:index] if index != -1 else other_details
        
        work_location = other_details[index+len(sep):] if index != -1 else "Unknown"
        work_style = "Unknown"
        if '(' in work_location and ')' in work_location:
            work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
            work_location = work_location[:work_location.rfind('(')].strip()
            
        skip = False
        if company in blacklisted_companies:
            skip = True
        elif job_id in rejected_jobs:
            skip = True
            
        return (job_id, title, company, work_location, work_style, skip)
    except Exception as e:
        return ("Unknown", "Unknown", "Unknown", "Unknown", "Unknown", True)

def extract_years_of_experience(text: str) -> int:
    matches = re.findall(re_experience, text)
    if len(matches) == 0: 
        return 0
    return max([int(match) for match in matches if int(match) <= 12])

def calculate_date_posted(time_string: str) -> datetime | None:
    time_string = time_string.strip()
    now = datetime.now()
    match = re.search(r'(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago', time_string, re.IGNORECASE)

    if match:
        try:
            value = int(match.group(1))
            unit = match.group(2).lower()
            if 'second' in unit: return now - timedelta(seconds=value)
            elif 'minute' in unit: return now - timedelta(minutes=value)
            elif 'hour' in unit: return now - timedelta(hours=value)
            elif 'day' in unit: return now - timedelta(days=value)
            elif 'week' in unit: return now - timedelta(weeks=value)
            elif 'month' in unit: return now - timedelta(days=value * 30)
            elif 'year' in unit: return now - timedelta(days=value * 365)
        except: pass
    return None
