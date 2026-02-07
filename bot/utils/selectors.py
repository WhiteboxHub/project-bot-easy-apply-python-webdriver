import yaml
from pathlib import Path

# Load Selectors from YAML
SELECTORS_CONFIG_PATH = Path("bot/config/selectors.yaml")
if SELECTORS_CONFIG_PATH.exists():
    with open(SELECTORS_CONFIG_PATH, "r") as f:
        SELECTORS_CONFIG = yaml.safe_load(f)
else:
    SELECTORS_CONFIG = {}

class SelectorsClass:
    """
    Dynamically loads constants from selectors.yaml.
    """
    def __init__(self, config):
        self._consts = config.get("constants", {})

    def __getattr__(self, name):
        if name in self._consts:
            return self._consts[name]
        return ""

    # Legacy compatibility for common attributes
    @property
    def JOB_LISTINGS(self): return self._consts.get("JOB_LISTINGS", "//li[@data-occludable-job-id]")
    
    # Redundant keywords (moved to form_filling.yaml)
    LABEL_PHONE = []
    LABEL_FIRST_NAME = []
    LABEL_LAST_NAME = []
    LABEL_EMAIL = []
    LABEL_CITY = []
    LABEL_ZIPCODE = []
    LABEL_EXPERIENCE = []
    LABEL_SALARY = []

# Instantiate the global Selectors object
Selectors = SelectorsClass(SELECTORS_CONFIG)

class SelectorRegistry:
    """
    Registry to manage selectors and their fallbacks.
    Loaded from YAML and synced with DuckDB.
    """
    _registry = SELECTORS_CONFIG.get("registry", {})

    @classmethod
    def get(cls, name):
        return cls._registry.get(name, [])

    @classmethod
    def sync_with_db(cls, db):
        """
        Robust Sync:
        1. Push any selectors from YAML that are MISSING in the DB.
        2. Load all selectors from DB and use them as the final truth (overriding YAML).
        """
        try:
            db_selectors = db.load_selectors()
            
            # 1. Check for YAML keys not in DB
            to_save = {}
            for k, v in cls._registry.items():
                if k not in db_selectors:
                    to_save[k] = v
            
            if to_save:
                db.save_selectors(to_save)
                print(f"✅ Added {len(to_save)} new selectors from YAML to DuckDB.")
                # Refresh db_selectors
                db_selectors = db.load_selectors()

            # 2. Use DB values for everything that exists in DB
            for k, v in db_selectors.items():
                cls._registry[k] = [tuple(item) for item in v]
            
            print("✅ Selectors synced. Database overrides are active.")
        except Exception as e:
            print(f"⚠️ Selector DB sync failed: {e}")
            pass
