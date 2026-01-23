import yaml
import os
from pathlib import Path
from typing import List, Dict, Optional
from bot.utils.logger import logger

class Candidate:
    """Represents a single candidate with their configuration"""
    
    def __init__(self, data: dict):
        self.id = data['id']
        self.name = data['name']
        self.enabled = data.get('enabled', True)
        
        # Credentials
        creds = data.get('credentials', {})
        self.email = creds.get('email', '')
        self.password = creds.get('password', '') or os.getenv(f"{self.id.upper()}_PASSWORD", '')
        self.phone = creds.get('phone', '')
        
        # Profile
        self.profile_path = data.get('profile_path', '')
        
        # Uploads
        self.uploads = data.get('uploads', {})
        
        # Search parameters
        search = data.get('search', {})
        self.positions = search.get('positions', [])
        self.locations = search.get('locations', [])
        self.salary = search.get('salary', 60000)
        self.rate = search.get('rate', 25)
        self.experience_level = search.get('experience_level', [])
        
        # Preferences
        prefs = data.get('preferences', {})
        self.max_applications_per_run = prefs.get('max_applications_per_run', 10)
        self.cooldown_seconds = prefs.get('cooldown_seconds', 90)
        self.dry_run = prefs.get('dry_run', True)
        self.blacklist = prefs.get('blacklist', [])
        self.blacklist_titles = prefs.get('blacklist_titles', [])
    
    def validate(self) -> tuple[bool, str]:
        """Validate candidate configuration"""
        if not self.email:
            return False, f"Candidate {self.id}: Email is required"
        
        if not self.password:
            return False, f"Candidate {self.id}: Password is required (use .env or config)"
        
        if not self.phone:
            return False, f"Candidate {self.id}: Phone number is required"
        
        if not self.positions:
            return False, f"Candidate {self.id}: At least one position is required"
        
        if not self.locations:
            return False, f"Candidate {self.id}: At least one location is required"
        
        # Check if resume exists
        resume_path = self.uploads.get('Resume', '')
        if resume_path and not Path(resume_path).exists():
            return False, f"Candidate {self.id}: Resume not found at {resume_path}"
        
        return True, "Valid"
    
    def get_positions(self) -> List[str]:
        return self.positions
    
    def get_locations(self) -> List[str]:
        return self.locations
    
    def get_max_applications(self) -> int:
        return self.max_applications_per_run
    
    def get_cooldown(self) -> int:
        return self.cooldown_seconds
    
    def __repr__(self):
        return f"Candidate(id={self.id}, name={self.name}, enabled={self.enabled})"


class CandidateManager:
    """Manages multiple candidate configurations"""
    
    def __init__(self, config_path: str = "config/candidates.yaml"):
        self.config_path = config_path
        self.candidates: Dict[str, Candidate] = {}
        self._load_candidates()
    
    def _load_candidates(self):
        """Load candidates from YAML configuration"""
        if not Path(self.config_path).exists():
            logger.warning(
                f"Candidates config not found: {self.config_path}. Creating example file.",
                step="candidate_manager",
                event="config_missing"
            )
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data or 'candidates' not in data:
                logger.warning(
                    "No candidates found in config",
                    step="candidate_manager",
                    event="no_candidates"
                )
                return
            
            for candidate_data in data.get('candidates', []):
                candidate = Candidate(candidate_data)
                
                # Validate candidate
                is_valid, message = candidate.validate()
                if not is_valid:
                    logger.error(
                        f"Invalid candidate configuration: {message}",
                        step="candidate_manager",
                        event="validation_failed"
                    )
                    continue
                
                self.candidates[candidate.id] = candidate
                
                status = "enabled" if candidate.enabled else "disabled"
                logger.info(
                    f"Loaded candidate: {candidate.name} ({status})",
                    step="candidate_manager",
                    event="candidate_loaded"
                )
        
        except yaml.YAMLError as e:
            logger.error(
                f"Failed to parse candidates config: {e}",
                step="candidate_manager",
                event="yaml_error",
                exception=e
            )
        except Exception as e:
            logger.error(
                f"Failed to load candidates: {e}",
                step="candidate_manager",
                event="load_error",
                exception=e
            )
    
    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Get a specific candidate by ID"""
        return self.candidates.get(candidate_id)
    
    def list_candidates(self, enabled_only: bool = False) -> List[Candidate]:
        """List all candidates"""
        candidates = list(self.candidates.values())
        if enabled_only:
            candidates = [c for c in candidates if c.enabled]
        return candidates
    
    def get_enabled_candidates(self) -> List[Candidate]:
        """Get only enabled candidates"""
        return self.list_candidates(enabled_only=True)
    
    def count(self) -> int:
        """Get total number of candidates"""
        return len(self.candidates)
    
    def count_enabled(self) -> int:
        """Get number of enabled candidates"""
        return len(self.get_enabled_candidates())
