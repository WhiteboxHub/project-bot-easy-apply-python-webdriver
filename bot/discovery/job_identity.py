from selenium.webdriver.common.by import By
from bot.utils.logger import logger

class JobIdentity:
    @staticmethod
    def extract_job_id(element):
        """
        Extracts job ID from a job card element.
        Tries 'data-job-id' attribute explicitly.
        """
        try:
            job_id = element.get_attribute("data-job-id")
            if job_id:
                return job_id
            
            # Fallback parsing if needed? 
            # Usually data-job-id is reliable on LinkedIn search results.
            # Only if extraction fails entirely.
            
            return None
        except Exception as e:
            logger.debug(f"Failed to extract job ID: {e}", step="extract_job_id")
            return None
