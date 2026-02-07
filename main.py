import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import pyautogui

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.core.candidate_manager import load_candidate, extract_variables, get_candidate_profile_slug
from bot.core.browser import init_driver, find_default_profile_directory
from bot.core.session import login_LN, is_logged_in_LN
from bot.core.metrics import load_counts, get_candidate_counts, update_candidate_count, save_counts
from bot.core.execution_guard import execution_guard, apply_cooldown
from bot.core.dry_run import discard_application
from bot.discovery.search import get_base_search_url
from bot.discovery.job_identity import get_job_main_details
from bot.application.workflow import process_job_application, get_job_description
from bot.persistence.store import PersistenceManager
from bot.utils.logger import print_lg
from bot.utils.delays import buffer

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


def is_likely_authwall(driver):
    """Lightweight auth-wall detection without navigation side effects."""
    url = (driver.current_url or "").lower()
    if any(p in url for p in ["/login", "/authwall", "/checkpoint", "/signup"]):
        return True
    try:
        if driver.find_elements(By.XPATH, "//input[@id='username' or @name='session_key']"):
            return True
        if driver.find_elements(By.XPATH, "//input[@id='password' or @name='session_password']"):
            return True
    except Exception:
        pass
    return False


def find_job_cards(driver):
    """Try all configured job listing selectors and return the first non-empty result."""
    from bot.utils.selectors import SelectorRegistry, Selectors

    selectors = SelectorRegistry.get("job_listings") or [("XPATH", Selectors.JOB_LISTINGS)]
    for strategy, selector in selectors:
        try:
            if strategy == "XPATH":
                items = driver.find_elements(By.XPATH, selector)
            elif strategy == "CSS":
                items = driver.find_elements(By.CSS_SELECTOR, selector)
            else:
                items = []
            if items:
                print_lg(f"DEBUG: Job selector matched -> {strategy}: {selector}")
                return items
        except Exception:
            continue
    return []

def quit_driver(driver):
    """Safely quit the driver, ignoring common Windows handle errors."""
    if not driver: return
    try:
        driver.quit()
    except Exception as e:
        # Ignore common Windows/UC cleanup errors
        err_msg = str(e).lower()
        if any(x in err_msg for x in ["handle is invalid", "invalid session id", "connection reset", "no such session"]):
            pass
        else:
            print(f"Error quitting driver: {e}")

def is_driver_alive(driver):
    try:
        driver.title
        return True
    except:
        return False

def main():
    load_dotenv()
    driver = None
    counts_data = {} # Initialize to avoid UnboundLocalError
    
    try:
        # 1. Load Configuration
        # Support CLI argument for candidate (run_all.py needs this)
        candidate_arg = sys.argv[1] if len(sys.argv) > 1 else None
        cfg = load_candidate(candidate_arg)
        vars = extract_variables(cfg)
        candidate_name = vars.get('first_name', 'default').lower()
        
        print_lg(f"DEBUG: Loaded candidate {candidate_name}")
        print_lg(f"DEBUG: Phone Number in vars: '{vars.get('phone_number')}'")
        print_lg(f"DEBUG: Email in vars: '{vars.get('email')}'")
        
        # 2. Initialize Metrics & Persistence
        counts_data = load_counts()
        c_counts = get_candidate_counts(candidate_name, counts_data)
        
        # Initialize database and CSV logging path
        csv_filename = vars.get('file_name', 'applied_jobs.csv')
        csv_path = os.path.join("output", csv_filename)
        db = PersistenceManager(csv_path=csv_path)
        
        # Sync selectors from code to DB (and allow DB to override)
        from bot.utils.selectors import SelectorRegistry
        SelectorRegistry.sync_with_db(db)
        
        # 3. Initialize Browser
        # Always use a dedicated persistent per-candidate profile directory.
        # This avoids temporary guest sessions and keeps login cookies per candidate.
        project_root = os.path.dirname(os.path.abspath(__file__))
        profile_root = os.path.join(project_root, "chrome_profiles")
        os.makedirs(profile_root, exist_ok=True)

        candidate_profile_slug = get_candidate_profile_slug(cfg)
        user_data_dir = os.path.join(profile_root, candidate_profile_slug)
        os.makedirs(user_data_dir, exist_ok=True)
        print_lg(f"🌐 Using persistent browser profile: {user_data_dir}")

        driver = init_driver(
            headless=vars.get('run_in_background', False),
            user_data_dir=user_data_dir,
            proxy_url=os.getenv("PROXY_URL"),
            disable_extensions=vars.get('disable_extensions', False)
        )
        wait = WebDriverWait(driver, 10)
        actions = ActionChains(driver)
        
        # 4. Login
        # Prioritize YAML credentials as per user request
        username = vars.get('username')
        password = vars.get('password')
        
        if not username or not password:
            print_lg("⚠️ Warning: Username or Password missing in YAML. Falling back to .env if available...")
            username = username or os.getenv("LINKEDIN_USERNAME")
            password = password or os.getenv("LINKEDIN_PASSWORD")

        if not is_logged_in_LN(driver):
            login_LN(driver, wait, username, password)
        
        # 5. Main Search Loop
        search_terms = vars.get('search_terms', [])
        search_location = vars.get('search_location', '')
        
        for term in search_terms:
            if not is_driver_alive(driver):
                print_lg("❌ Browser session lost. Exiting.")
                break

            if not execution_guard(vars.get('dry_run'), vars.get('max_applications'), c_counts.get('easy_applied', 0)):
                break
                
            print_lg(f"\n🔍 Starting search for: {term}")
            url = get_base_search_url(term, vars)
            driver.get(url)
            buffer(3)
            
            if not is_driver_alive(driver): break

            if search_location:
                from bot.discovery.search import set_search_location
                set_search_location(driver, actions, search_location)
                buffer(5) # Wait for results after location change
                
                if vars.get('pause_after_filters', True):
                    print_lg("Pausing after filters for user inspection...")
                    if "Look's good, Continue" != pyautogui.confirm(
                        "These are your configured search results and filter. Please check your results.", 
                        "Please check your results", 
                        ["Turn off Pause after search", "Look's good, Continue"]
                    ):
                        print_lg("Search review cancelled by user or chose to turn off pause.")
                        # If they choose "Turn off Pause after search", we could update vars, but for now just continue
            
            # Find all job listings (limit to switch_number)
            try:
                job_listings = find_job_cards(driver)

                if len(job_listings) == 0:
                    print_lg(f"⚠️ No jobs found initially for '{term}'. Retrying after scroll...")
                    try:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
                    except Exception:
                        pass
                    buffer(2)
                    job_listings = find_job_cards(driver)

                if len(job_listings) == 0:
                    print_lg(f"DEBUG: URL={driver.current_url}")
                    print_lg(f"DEBUG: Title={driver.title}")
                    if is_likely_authwall(driver):
                        print_lg("❌ Looks like LinkedIn auth wall/login page. Search results unavailable until logged in.")

                print_lg(f"Found {len(job_listings)} jobs for '{term}'.")
                
                applied_this_term = 0
                max_this_term = vars.get('switch_number', 10)
                current_page = 1
                
                while applied_this_term < max_this_term:
                    if not is_driver_alive(driver): break
                    
                    job_listings = find_job_cards(driver)
                    if len(job_listings) == 0:
                        print_lg(f"No more jobs found on page {current_page}.")
                        break

                    print_lg(f"Processing page {current_page} ({len(job_listings)} jobs found)...")
                    
                    for job_card in job_listings:
                        if applied_this_term >= max_this_term: break
                        
                        job_id, title, company, loc, style, skip = get_job_main_details(driver, job_card, set(), set())
                        
                        if skip or db.is_applied(job_id):
                            continue
                            
                        # Click job to load description
                        try:
                            job_card.click()
                            buffer(2)
                        except: continue
                        
                        # Check description
                        desc, exp, skip_desc, reason, msg = get_job_description(driver, vars)
                        if skip_desc:
                            print_lg(f"Skipping {title}: {reason} - {msg}")
                            continue
                            
                        # Process application
                        success = process_job_application(driver, actions, wait, job_id, title, company, vars, db, counts_data)
                        
                        if success:
                            db.log_application(job_id, title, company, "Success", "Applied", url, candidate_name)
                            update_candidate_count(candidate_name, "easy_applied", counts_data)
                            applied_this_term += 1
                            apply_cooldown(vars.get('submission_cooldown', 30))
                        else:
                            db.log_application(job_id, title, company, "Failed", "Failed during process", url, candidate_name)

                    # Pagination: try to go to next page
                    if applied_this_term < max_this_term:
                        current_page += 1
                        from bot.utils.selectors import Selectors
                        
                        # Scroll to bottom of job list to reveal pagination
                        try:
                            # Try searching for a known pagination container or just scroll the job list
                            print_lg(f"Scrolling to reveal page {current_page}...")
                            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            buffer(2)
                        except: pass

                        next_page_xpath = Selectors.PAGINATION_NEXT.format(page=current_page)
                        try:
                            next_button = driver.find_element(By.XPATH, next_page_xpath)
                            print_lg(f"Moving to search page {current_page}...")
                            next_button.click()
                            buffer(5) # Wait for page to load
                        except:
                            print_lg(f"No pagination button for page {current_page} found. Ending search for '{term}'.")
                            break
                    else:
                        break
                        
            except Exception as e:
                print_lg(f"Error in searchTerm '{term}': {e}")
                continue
            
        print_lg("\n✅ Bot run finished.")
        
    except Exception as e:
        print_lg(f"🛑 Critical Error in main: {e}")
        sys.exit(1)
    finally:
        save_counts(counts_data)
        if 'db' in locals(): db.close()
        quit_driver(driver)

if __name__ == "__main__":
    main()
