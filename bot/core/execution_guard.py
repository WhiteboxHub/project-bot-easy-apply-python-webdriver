from time import sleep
from bot.utils.logger import print_lg

def execution_guard(dry_run=False, max_applications=50, current_applications=0):
    """Check if we can proceed with an application."""
    if current_applications >= max_applications:
        print_lg(f"🛑 Limit Reached: Applied to {current_applications} jobs today.")
        return False
    return True

def apply_cooldown(seconds=30):
    """Apply a cooldown period between applications."""
    if seconds > 0:
        print_lg(f"⏳ Cooldown: Waiting {seconds}s...")
        sleep(seconds)
