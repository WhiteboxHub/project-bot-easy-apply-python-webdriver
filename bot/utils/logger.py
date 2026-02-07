import logging
import os
import sys
from pprint import pprint

# Force UTF-8 for stdout and stderr on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Fallback path for simple logging
__logs_file_path = "logs/log.txt"
STRUCTURED_LOG_PATH = "logs/bot_structured.log"

# Ensure log directory exists
os.makedirs("logs", exist_ok=True)

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(STRUCTURED_LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("LinkedInBot")

def log_step(step_name, status, job_id=None, details=None):
    """
    Structured logging for bot steps.
    """
    msg = f"Step: {step_name} | Status: {status}"
    if job_id:
        msg += f" | JobID: {job_id}"
    if details:
        msg += f" | Details: {details}"
    
    if status.lower() == "failed" or status.lower() == "error":
        logger.error(msg)
    elif status.lower() == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)

def print_lg(*msgs, end="\n", pretty=False, flush=False):
    """
    Classic print and log function.
    """
    try:
        # Move strings into a single list to iterate
        for message in msgs:
            msg_str = str(message)
            try:
                pprint(message) if pretty else print(msg_str, end=end, flush=flush)
            except UnicodeEncodeError:
                # If printing emoji fails, strip it or print safe version
                safe_msg = msg_str.encode('ascii', 'ignore').decode('ascii')
                pprint(safe_msg) if pretty else print(safe_msg, end=end, flush=flush)
            
            # Ensure directory exists before writing
            log_dir = os.path.dirname(__logs_file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
                
            with open(__logs_file_path, 'a+', encoding="utf-8") as file:
                file.write(msg_str + end)
    except Exception as e:
        # Fallback print if even file writing fails
        print(f"FAILED TO LOG: {e}")
