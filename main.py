import yaml
import logging
from bot.utils.logger import logger

from bot.core.browser import Browser
from bot.core.session import Session
from bot.application.workflow import Workflow
from bot.discovery.search import Search
from bot.core.execution_guard import ExecutionGuard
from bot.core.dry_run import DryRun
from bot.core.metrics import Metrics
import atexit
from dotenv import load_dotenv

load_dotenv()



from datetime import datetime
import os


if __name__ == '__main__':


    with open("config.yaml", 'r') as stream:
        try:
            parameters = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            raise exc

    # Validate parameters
    assert len(parameters['positions']) > 0
    assert len(parameters['locations']) > 0
    assert parameters['username'] is not None
    assert parameters['password'] is not None
    assert parameters['phone_number'] is not None

    uploads = parameters.get('uploads', {})
    blacklist = parameters.get('blacklist', [])
    blacklist_titles = parameters.get('blackListTitles', [])
    experience_level = parameters.get('experience_level', [])
    
    # Execution Guard & Dry Run Configuration
    execution_config = parameters.get('execution', {})
    max_apps = execution_config.get('max_applications_per_run', 10)
    cooldown = execution_config.get('cooldown_seconds', 90)
    is_dry_run = execution_config.get('dry_run', True)

    logger.info("Starting Easy Apply Bot", step="init")
    
    execution_guard = ExecutionGuard(max_apps, cooldown)
    dry_run = DryRun(is_dry_run)
    metrics = Metrics()
    
    # Register summary on exit
    atexit.register(metrics.print_summary)



    # Initialize Core Components
    browser = Browser() # Loads default profile
    session = Session(browser.driver)
    
    # Login
    session.login(parameters['username'], parameters['password'])

    # Application & Search Components
    workflow = Workflow(browser, uploads, blacklist_titles, execution_guard=execution_guard, dry_run=dry_run, metrics=metrics)

    # Patch phone number into workflow logic (simplification for now) but ideally passed properly

    # For now we will pass it in the loop or make it part of workflow init
    
    # We need to make sure workflow knows the phone number if it's used in 'fill_out_fields' which is called by 'apply_to_job'
    # In my Search refactor I passed phone number. But wait, I passed it as a string literal placeholders.
    # Let me fix that injection or architecture flaw. 
    # Actually, let's just modify the Search class to accept the phone number and pass it down.
    
    search = Search(browser, workflow, blacklist, experience_level, parameters['phone_number'])
    
    # Wait, I need to update Search logic to actually use this phone number.
    # I'll update search.py in the next step to fix the placeholder. 
    
    locations = [l for l in parameters['locations'] if l is not None]
    positions = [p for p in parameters['positions'] if p is not None]

    search.start_apply(positions, locations)
