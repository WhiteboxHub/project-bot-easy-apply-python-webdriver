import yaml
import logging
import argparse
import uuid
from datetime import datetime
from bot.utils.logger import logger

from bot.core.browser import Browser
from bot.core.session import Session
from bot.core.candidate_manager import CandidateManager
from bot.core.proxy_manager import ProxyManager
from bot.application.workflow import Workflow
from bot.discovery.search import Search
from bot.core.execution_guard import ExecutionGuard
from bot.core.dry_run import DryRun
from bot.core.metrics import Metrics
from bot.persistence.store import Store
import atexit
from dotenv import load_dotenv

load_dotenv()


def run_candidate(candidate, proxy_manager, store, args):
    """Run bot for a single candidate"""
    
    run_id = str(uuid.uuid4())
    logger.info(f"Starting run for candidate: {candidate.name}", step="main", event="run_start")
    
    # Get proxy if enabled
    proxy_config = proxy_manager.get_proxy() if proxy_manager.enabled else None
    proxy_name = proxy_config.name if proxy_config else "none"
    
    # Record run start
    store.con.execute(
        "INSERT INTO runs (run_id, candidate_id, started_at, proxy_used) VALUES (?, ?, ?, ?)",
        [run_id, candidate.id, datetime.now(), proxy_name]
    )
    
    # Initialize metrics
    metrics = Metrics()
    atexit.register(metrics.print_summary)
    
    # Initialize execution guard with candidate preferences
    execution_guard = ExecutionGuard(
        max_apps=candidate.get_max_applications(),
        cooldown=candidate.get_cooldown()
    )
    
    # Initialize dry run mode
    dry_run = DryRun(candidate.dry_run or args.dry_run)
    
    try:
        # Initialize browser with candidate profile and proxy
        browser = Browser(
            profile_path=candidate.profile_path,
            proxy_config=proxy_config
        )
        
        # Initialize session
        session = Session(browser.driver)
        
        # Login with candidate credentials
        session.login(candidate.email, candidate.password)
        
        # Initialize workflow
        workflow = Workflow(
            browser,
            candidate.uploads,
            candidate.blacklist_titles,
            execution_guard=execution_guard,
            dry_run=dry_run,
            metrics=metrics
        )
        
        # Initialize search
        search = Search(
            browser,
            workflow,
            candidate.blacklist,
            candidate.experience_level,
            candidate.phone
        )
        
        # Start applying
        positions = candidate.get_positions()
        locations = candidate.get_locations()
        
        logger.info(
            f"Searching for {len(positions)} positions in {len(locations)} locations",
            step="main",
            event="search_start"
        )
        
        search.start_apply(positions, locations)
        
        # Update run completion
        store.con.execute(
            "UPDATE runs SET completed_at = ?, applications_submitted = ? WHERE run_id = ?",
            [datetime.now(), metrics.submitted, run_id]
        )
        
        logger.info(
            f"Completed run for {candidate.name}: {metrics.submitted} applications submitted",
            step="main",
            event="run_complete"
        )
        
        # Notify proxy manager of application completion
        if proxy_manager.enabled:
            for _ in range(metrics.submitted):
                proxy_manager.on_application_complete()
        
    except Exception as e:
        logger.error(
            f"Run failed for {candidate.name}: {e}",
            step="main",
            event="run_error",
            exception=e
        )
        
        # Update run with failure
        store.con.execute(
            "UPDATE runs SET completed_at = ?, applications_failed = 1 WHERE run_id = ?",
            [datetime.now(), run_id]
        )
    
    finally:
        # Clean up
        if 'browser' in locals():
            try:
                browser.driver.quit()
            except:
                pass


if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='LinkedIn Easy Apply Bot 2.0 - Multi-Candidate Edition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all candidates
  python main.py --list-candidates
  
  # Run for specific candidate
  python main.py --candidate candidate_001
  
  # Run for all enabled candidates
  python main.py --all
  
  # Dry run mode
  python main.py --candidate candidate_001 --dry-run
  
  # Show proxy stats
  python main.py --proxy-stats
        """
    )
    
    parser.add_argument(
        '--candidate',
        type=str,
        help='Candidate ID to run (from candidates.yaml)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run for all enabled candidates sequentially'
    )
    
    parser.add_argument(
        '--list-candidates',
        action='store_true',
        help='List all configured candidates'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run in dry-run mode (no actual submissions)'
    )
    
    parser.add_argument(
        '--proxy-stats',
        action='store_true',
        help='Show proxy configuration and statistics'
    )
    
    args = parser.parse_args()
    
    # Initialize managers
    candidate_manager = CandidateManager()
    proxy_manager = ProxyManager()
    store = Store()
    
    # Handle list candidates
    if args.list_candidates:
        candidates = candidate_manager.list_candidates()
        if not candidates:
            print("No candidates configured. Please edit config/candidates.yaml")
        else:
            print(f"\n{'ID':<20} {'Name':<25} {'Email':<30} {'Status':<10}")
            print("-" * 85)
            for c in candidates:
                status = "✓ Enabled" if c.enabled else "✗ Disabled"
                print(f"{c.id:<20} {c.name:<25} {c.email:<30} {status:<10}")
            print(f"\nTotal: {len(candidates)} candidates ({candidate_manager.count_enabled()} enabled)\n")
        exit(0)
    
    # Handle proxy stats
    if args.proxy_stats:
        stats = proxy_manager.get_stats()
        print(f"\nProxy Configuration:")
        print(f"  Enabled: {stats['enabled']}")
        print(f"  Current Proxy: {stats['current_proxy']}")
        print(f"  Total Pools: {stats['total_pools']}")
        print(f"  Healthy Pools: {stats['healthy_pools']}")
        print(f"  Rotation Strategy: {stats['rotation_strategy']}")
        print(f"  Application Count: {stats['application_count']}\n")
        exit(0)
    
    # Validate we have candidates
    if candidate_manager.count() == 0:
        print("❌ No candidates configured!")
        print("Please create config/candidates.yaml with at least one candidate.")
        print("See config/candidates.yaml.example for template.")
        exit(1)
    
    # Determine which candidates to run
    candidates_to_run = []
    
    if args.all:
        candidates_to_run = candidate_manager.get_enabled_candidates()
        if not candidates_to_run:
            print("❌ No enabled candidates found!")
            print("Please enable at least one candidate in config/candidates.yaml")
            exit(1)
        print(f"Running for {len(candidates_to_run)} enabled candidates...")
    
    elif args.candidate:
        candidate = candidate_manager.get_candidate(args.candidate)
        if not candidate:
            print(f"❌ Candidate not found: {args.candidate}")
            print("\nAvailable candidates:")
            for c in candidate_manager.list_candidates():
                print(f"  - {c.id}: {c.name}")
            exit(1)
        
        if not candidate.enabled:
            print(f"⚠️  Warning: Candidate {candidate.id} is disabled")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                exit(0)
        
        candidates_to_run = [candidate]
    
    else:
        # Default: run first enabled candidate
        enabled = candidate_manager.get_enabled_candidates()
        if enabled:
            candidates_to_run = [enabled[0]]
            print(f"No candidate specified, using first enabled: {enabled[0].name}")
        else:
            print("❌ No enabled candidates found!")
            print("Use --candidate <id> to specify a candidate, or --all to run all enabled candidates")
            exit(1)
    
    # Run for each candidate
    logger.info(
        f"Starting LinkedIn Easy Apply Bot for {len(candidates_to_run)} candidate(s)",
        step="main",
        event="bot_start"
    )
    
    for i, candidate in enumerate(candidates_to_run, 1):
        print(f"\n{'='*80}")
        print(f"Running {i}/{len(candidates_to_run)}: {candidate.name} ({candidate.id})")
        print(f"{'='*80}\n")
        
        # Reset proxy session for new candidate if using per_candidate strategy
        if proxy_manager.rotation_strategy == "per_candidate":
            proxy_manager.reset_session()
        
        run_candidate(candidate, proxy_manager, store, args)
        
        # Pause between candidates if running multiple
        if i < len(candidates_to_run):
            import time
            pause_time = 60  # 1 minute between candidates
            print(f"\nPausing {pause_time}s before next candidate...")
            time.sleep(pause_time)
    
    logger.info(
        "All candidates completed",
        step="main",
        event="bot_complete"
    )
