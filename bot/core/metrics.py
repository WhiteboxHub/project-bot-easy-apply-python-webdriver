import json
import os
from datetime import datetime

COUNTS_FILE = "data/counts.json"

def load_counts():
    """Load persistent counts for all candidates from JSON file."""
    if os.path.exists(COUNTS_FILE):
        try:
            with open(COUNTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_counts(counts_data):
    """Save persistent counts for all candidates to JSON file."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(COUNTS_FILE), exist_ok=True)
    with open(COUNTS_FILE, "w") as f:
        json.dump(counts_data, f, indent=4)

def get_candidate_counts(candidate_name, counts_data):
    """Get counts for a specific candidate, initialize if not exists. Reset if new day."""
    today = datetime.now().strftime("%Y-%m-%d")
    
    if candidate_name not in counts_data:
        counts_data[candidate_name] = {}
    
    c_data = counts_data[candidate_name]
    
    if c_data.get("last_run_date") != today:
        c_data["last_run_date"] = today
        c_data["easy_applied"] = 0
        c_data["external"] = 0
        c_data["failed"] = 0
        c_data["skipped"] = 0
    
    return c_data

def update_candidate_count(candidate_name, count_type, counts_data):
    """Update a specific count for a candidate and save."""
    c_data = get_candidate_counts(candidate_name, counts_data)
    c_data[count_type] = c_data.get(count_type, 0) + 1
    save_counts(counts_data)
    return counts_data
