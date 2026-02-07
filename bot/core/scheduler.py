import time
from bot.utils.logger import print_lg

def wait_for_next_cycle(seconds=3600):
    """Wait before starting the next search cycle."""
    print_lg(f"Cycle completed. Waiting {seconds/60:.1f} minutes before next run...")
    time.sleep(seconds)
