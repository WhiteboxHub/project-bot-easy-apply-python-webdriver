

import os
import yaml
import pyautogui
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "assets", "candidates")

def list_candidates():
    """Return all YAML candidate files."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        return []
    
    return [f for f in os.listdir(CONFIG_DIR) if f.endswith(".yaml") or f.endswith(".yml")]

def choose_candidate():
    """Ask user to choose a candidate profile."""
    candidates = list_candidates()

    if not candidates:
        pyautogui.alert(
            "No candidate YAML files found in config/candidates/\n\n"
            "Create at least one yaml file first!",
            "Missing Candidate Files"
        )
        raise FileNotFoundError("No YAML files found in config/candidates/")

    if len(candidates) == 1:
        # Only one candidate → auto-select
        print(f"Auto-selecting only candidate: {candidates[0]}")
        return candidates[0]

    # Show selection dialog
    choice_name = pyautogui.confirm(
        "Select candidate profile to run the bot:",
        "Choose Candidate",
        candidates
    )

    if not choice_name:
        raise Exception("Candidate selection cancelled!")

    return choice_name

def load_yaml(path):
    """Load YAML and return dict."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing YAML file {path}: {e}")
    except FileNotFoundError:
        raise Exception(f"YAML file not found: {path}")

def load_candidate(candidate_name=None):
    """
    Loads the chosen candidate YAML 
    and returns it as cfg dictionary.
    
    Args:
        candidate_name (str, optional): Name of candidate file without extension
                                      If None, will prompt user to choose
    
    Returns:
        dict: Configuration dictionary
    """
    if candidate_name:
        # Direct load if name provided
        candidate_file = f"{candidate_name}.yaml" if not candidate_name.endswith('.yaml') else candidate_name
        full_path = os.path.join(CONFIG_DIR, candidate_file)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Candidate file not found: {full_path}")
    else:
        # Let user choose
        candidate_file = choose_candidate()
        full_path = os.path.join(CONFIG_DIR, candidate_file)
    
    cfg = load_yaml(full_path)
    
    if not cfg:
        raise ValueError(f"The configuration file '{candidate_file}' is empty or invalid YAML.")

    # Add metadata
    cfg['_meta'] = {
        'candidate_file': candidate_file,
        'config_path': full_path
    }
    
    print(f"\n✅ Loaded Candidate Profile: {candidate_file}")
    return cfg

def get_candidate_name(cfg):
    """Extract candidate name from configuration."""
    candidate = cfg.get('candidate', {})
    return f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}".strip()

def get_candidate_profile_slug(cfg):
    """
    Build a stable filesystem-safe profile slug for browser session persistence.

    Preference order:
    1) Candidate yaml filename stem (from cfg['_meta']['candidate_file'])
    2) Candidate full name
    3) fallback: "default"
    """
    candidate_file = cfg.get('_meta', {}).get('candidate_file', '')
    if candidate_file:
        base = os.path.splitext(candidate_file)[0]
    else:
        base = get_candidate_name(cfg) or "default"

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", base.strip().lower())
    return slug.strip("_") or "default"

def extract_variables(cfg):
    """Extract all variables from YAML config to maintain compatibility."""
    variables = {}
    
    # Candidate section
    candidate = cfg.get('candidate', {})
    variables.update({
        'first_name': candidate.get('first_name', ''),
        'middle_name': candidate.get('middle_name', ''),
        'last_name': candidate.get('last_name', ''),
        'phone_number': candidate.get('phone_number', ''),
        'current_city': candidate.get('current_city', ''),
        'street': candidate.get('street', ''),
        'state': candidate.get('state', ''),
        'zipcode': candidate.get('zipcode', ''),
        'country': candidate.get('country', ''),
        'email': candidate.get('email', ''),
        'ethnicity': candidate.get('ethnicity', 'Decline'),
        'gender': candidate.get('gender', 'Decline'),
        'disability_status': candidate.get('disability_status', 'Decline'),
        'veteran_status': candidate.get('veteran_status', 'Decline'),
        'website': candidate.get('website', ''),
        'linkedin': candidate.get('linkedin', ''),
    })
    
    # Professional section
    professional = cfg.get('professional', {})
    variables.update({
        'default_resume_path': professional.get('resume_path', ''),
        'years_of_experience': professional.get('years_of_experience', '0'),
        'current_experience': professional.get('current_experience', 0),
        'require_visa': professional.get('require_visa', 'No'),
        'us_citizenship': professional.get('us_citizenship', 'Other'),
        'desired_salary': professional.get('desired_salary', 0),
        'current_ctc': professional.get('current_ctc', 0),
        'notice_period': professional.get('notice_period', 0),
        'linkedin_headline': professional.get('linkedin_headline', ''),
        'linkedin_summary': professional.get('linkedin_summary', ''),
        'cover_letter': professional.get('cover_letter', ''),
        'recent_employer': professional.get('recent_employer', 'Not Applicable'),
        'confidence_level': professional.get('confidence_level', '5'),
        'user_information_all': professional.get('user_information_all', ''),
    })
    
    # Job search section
    job_search = cfg.get('job_search', {})
    variables.update({
        'search_terms': job_search.get('search_terms', []),
        'search_location': job_search.get('search_location', ''),
        'switch_number': job_search.get('switch_number', 10),
        'randomize_search_order': job_search.get('randomize_search_order', False),
        'sort_by': job_search.get('sort_by', 'Most recent'),
        'date_posted': job_search.get('date_posted', 'Past week'),
        'salary': job_search.get('salary', ''),
        'easy_apply_only': job_search.get('easy_apply_only', True),
        'experience_level': job_search.get('experience_level', []),
        'job_type': job_search.get('job_type', []),
        'on_site': job_search.get('on_site', []),
        'companies': job_search.get('companies', []),
        'location': job_search.get('location', []),
        'industry': job_search.get('industry', []),
        'job_function': job_search.get('job_function', []),
        'job_titles': job_search.get('job_titles', []),
        'benefits': job_search.get('benefits', []),
        'commitments': job_search.get('commitments', []),
        'under_10_applicants': job_search.get('under_10_applicants', False),
        'in_your_network': job_search.get('in_your_network', False),
        'fair_chance_employer': job_search.get('fair_chance_employer', False),
        'pause_after_filters': job_search.get('pause_after_filters', True),
        'about_company_bad_words': job_search.get('about_company_bad_words', []),
        'about_company_good_words': job_search.get('about_company_good_words', []),
        'bad_words': job_search.get('bad_words', []),
        'security_clearance': job_search.get('security_clearance', False),
        'did_masters': job_search.get('did_masters', False),
    })
    
    # Secrets section
    secrets = cfg.get('secrets', {})
    variables.update({
        'username': secrets.get('username', ''),
        'password': secrets.get('password', ''),
        'use_AI': secrets.get('use_ai', False),
        'ai_provider': secrets.get('ai_provider', 'openai'),
        'llm_api_url': secrets.get('llm_api_url', ''),
        'llm_api_key': secrets.get('llm_api_key', ''),
        'llm_model': secrets.get('llm_model', 'gpt-3.5-turbo'),
        'stream_output': secrets.get('stream_output', False),
    })
    
    # Settings section
    settings = cfg.get('settings', {})
    variables.update({
        'close_tabs': settings.get('close_tabs', True),
        'follow_companies': settings.get('follow_companies', False),
        'run_non_stop': settings.get('run_non_stop', False),
        'alternate_sortby': settings.get('alternate_sortby', True),
        'cycle_date_posted': settings.get('cycle_date_posted', True),
        'stop_date_cycle_at_24hr': settings.get('stop_date_cycle_at_24hr', True),
        'file_name': settings.get('file_name', 'applied_jobs.csv'),
        'failed_file_name': settings.get('failed_file_name', 'failed_jobs.csv'),
        'logs_folder_path': settings.get('logs_folder_path', 'logs/'),
        'click_gap': settings.get('click_gap', 3),
        'run_in_background': settings.get('run_in_background', False),
        'disable_extensions': settings.get('disable_extensions', False),
        'safe_mode': settings.get('safe_mode', True),
        'smooth_scroll': settings.get('smooth_scroll', False),
        'keep_screen_awake': settings.get('keep_screen_awake', True),
        'stealth_mode': settings.get('stealth_mode', False),
        'pause_before_submit': settings.get('pause_before_submit', True),
        'pause_at_failed_question': settings.get('pause_at_failed_question', True),
        'overwrite_previous_answers': settings.get('overwrite_previous_answers', False),
        'showAiErrorAlerts': settings.get('show_ai_error_alerts', False),
        'dry_run': settings.get('dry_run', False),
        'max_applications': settings.get('max_applications', 50),
        'manual_mode': settings.get('manual_mode', True),
        'submission_cooldown': settings.get('submission_cooldown', 30),
        'comfortable_commuting': settings.get('comfortable_commuting', 'No'),
        'open_to_relocate': settings.get('open_to_relocate', 'No'),
        'willing_to_travel': settings.get('willing_to_travel', 'No'),
        'open_to_hybrid_remote': settings.get('open_to_hybrid_remote', 'Yes'),
        'max_modal_steps': settings.get('max_modal_steps', 12),
    })
    
    return variables
