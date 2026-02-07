import yaml
import urllib.parse
from pathlib import Path
from time import sleep
from selenium.webdriver.common.keys import Keys
from bot.application.form_filler import try_xp, text_input
from bot.utils.logger import print_lg
from bot.utils.delays import buffer

# Load Search Mappings
SEARCH_CONFIG_PATH = Path("bot/config/search_mappings.yaml")
if SEARCH_CONFIG_PATH.exists():
    with open(SEARCH_CONFIG_PATH, "r") as f:
        SEARCH_CONFIG = yaml.safe_load(f)
else:
    SEARCH_CONFIG = {}

def set_search_location(driver, actions, location_text):
    '''
    Function to set search location
    '''
    if location_text.strip():
        try:
            print_lg(f'Setting search location as: "{location_text.strip()}"')
            target_location = location_text.strip()
            search_location_ele = try_xp(driver, ".//input[@aria-label='City, state, or zip code' and not(@disabled)]", False)
            if not search_location_ele:
                 search_location_ele = try_xp(driver, ".//input[contains(@placeholder, 'Location')]", False)
            if not search_location_ele:
                 search_location_ele = try_xp(driver, ".//input[contains(@id, 'jobs-search-box-location')]", False)
            if not search_location_ele:
                 search_location_ele = try_xp(driver, ".//input[contains(@aria-label, 'Location')]", False)
            if not search_location_ele:
                 search_location_ele = try_xp(driver, ".//input[contains(@name, 'location')]", False)

            if not search_location_ele:
                raise Exception("Location input not found")
            
            text_input(actions, search_location_ele, target_location, "Search Location")
            sleep(2)

            current_value = (search_location_ele.get_attribute("value") or "").strip().lower()
            if target_location.lower() not in current_value:
                print_lg(f"⚠️ Location may not be applied. input_value='{current_value}', expected~='{target_location}'")
            else:
                print_lg(f"✅ Location set to: {current_value}")
        except Exception as e:
            try:
                try_xp(driver, ".//button[@aria-label='Cancel']")
                actions.send_keys(Keys.TAB, Keys.TAB).perform()
                actions.send_keys(location_text.strip()).perform()
                sleep(2)
                actions.send_keys(Keys.ENTER).perform()
                sleep(2)
                print_lg("⚠️ Used fallback flow for location update.")
            except:
                print_lg("Failed to update search location, continuing with default location!", e)

def get_base_search_url(search_term, vars):
    '''
    Constructs LinkedIn Job Search URL with filters using dynamic YAML mappings.
    '''
    params = {
        'keywords': search_term,
        'f_AL': 'true' if vars.get('easy_apply_only', True) else None
    }
    
    # 1. Date Posted
    date_val = vars.get('date_posted', '').lower()
    date_map = SEARCH_CONFIG.get('date_posted', {})
    for key, code in date_map.items():
        if key in date_val:
            params['f_TPR'] = code
            break
    
    # 2. Experience Level
    exp_levels = vars.get('experience_level', [])
    exp_map = SEARCH_CONFIG.get('experience_level', {})
    exp_ids = [exp_map[e.lower()] for e in exp_levels if e.lower() in exp_map]
    if exp_ids: params['f_E'] = ','.join(exp_ids)
    
    # 3. Job Type
    job_types = vars.get('job_type', [])
    jt_map = SEARCH_CONFIG.get('job_type', {})
    jt_ids = [jt_map[j.lower()] for j in job_types if j.lower() in jt_map]
    if jt_ids: params['f_JT'] = ','.join(jt_ids)
    
    # 4. Work Style (On-site/Remote/Hybrid)
    on_site = vars.get('on_site', [])
    wt_map = SEARCH_CONFIG.get('work_style', {})
    wt_ids = [wt_map[w.lower()] for w in on_site if w.lower() in wt_map]
    if wt_ids: params['f_WT'] = ','.join(wt_ids)

    # 5. Sort By
    sort_choice = vars.get('sort_by', '').lower()
    sort_map = SEARCH_CONFIG.get('sort_by', {})
    if sort_choice in sort_map:
        params['sortBy'] = sort_map[sort_choice]

    # Build URL
    base_url = "https://www.linkedin.com/jobs/search/?"
    clean_params = {k: v for k, v in params.items() if v is not None}
    
    return base_url + urllib.parse.urlencode(clean_params)
