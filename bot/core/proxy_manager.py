import yaml
import random
import time
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List
from bot.utils.logger import logger


class ProxyConfig:
    """Represents a single proxy configuration"""
    
    def __init__(self, data: dict):
        self.name = data['name']
        self.type = data.get('type', 'residential')
        self.host = data['host']
        self.port = data['port']
        self.username = data.get('username', '')
        self.password = data.get('password', '')
        self.country = data.get('country', '')
        self.enabled = data.get('enabled', True)
        self.failures = 0
        self.last_used = None
    
    def get_proxy_url(self) -> str:
        """Get proxy URL in format: http://user:pass@host:port"""
        if self.username and self.password:
            return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"http://{self.host}:{self.port}"
    
    def get_proxy_dict(self) -> Dict[str, str]:
        """Get proxy dictionary for requests library"""
        proxy_url = self.get_proxy_url()
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def get_chrome_proxy_string(self) -> str:
        """Get proxy string for Chrome --proxy-server argument"""
        return f"{self.host}:{self.port}"
    
    def __repr__(self):
        return f"ProxyConfig(name={self.name}, type={self.type}, country={self.country})"


class ProxyManager:
    """Manages proxy rotation and health checking"""
    
    def __init__(self, config_path: str = "config/proxy_config.yaml"):
        self.config_path = config_path
        self.enabled = False
        self.provider = "custom"
        self.rotation_strategy = "per_session"
        self.rotation_interval = 300
        self.apps_per_proxy = 5
        self.pools: List[ProxyConfig] = []
        self.current_proxy: Optional[ProxyConfig] = None
        self.health_check_config = {}
        self.fallback_config = {}
        self.application_count = 0
        self.session_start_time = time.time()
        
        self._load_config()
    
    def _load_config(self):
        """Load proxy configuration from YAML file"""
        if not Path(self.config_path).exists():
            logger.info(
                f"Proxy config not found: {self.config_path}. Proxies disabled.",
                step="proxy_manager",
                event="config_missing"
            )
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            proxy_config = data.get('proxy', {})
            self.enabled = proxy_config.get('enabled', False)
            
            if not self.enabled:
                logger.info("Proxy rotation disabled", step="proxy_manager", event="disabled")
                return
            
            self.provider = proxy_config.get('provider', 'custom')
            
            # Rotation settings
            rotation = proxy_config.get('rotation', {})
            self.rotation_strategy = rotation.get('strategy', 'per_session')
            self.rotation_interval = rotation.get('interval', 300)
            self.apps_per_proxy = rotation.get('applications_per_proxy', 5)
            
            # Load proxy pools
            for pool_data in proxy_config.get('pools', []):
                if not pool_data.get('enabled', True):
                    continue
                
                # Substitute environment variables in credentials
                pool_data = self._substitute_env_vars(pool_data)
                proxy = ProxyConfig(pool_data)
                self.pools.append(proxy)
            
            # Health check settings
            self.health_check_config = proxy_config.get('health_check', {})
            
            # Fallback settings
            self.fallback_config = proxy_config.get('fallback', {})
            
            logger.info(
                f"Loaded {len(self.pools)} proxy pools with {self.rotation_strategy} rotation",
                step="proxy_manager",
                event="config_loaded"
            )
        
        except yaml.YAMLError as e:
            logger.error(
                f"Failed to parse proxy config: {e}",
                step="proxy_manager",
                event="yaml_error",
                exception=e
            )
        except Exception as e:
            logger.error(
                f"Failed to load proxy config: {e}",
                step="proxy_manager",
                event="load_error",
                exception=e
            )
    
    def _substitute_env_vars(self, pool_data: dict) -> dict:
        """Substitute environment variables in proxy configuration"""
        # Replace {env_var} patterns with environment variables
        for key in ['username', 'password']:
            if key in pool_data and pool_data[key]:
                value = pool_data[key]
                # Check if it's an env var pattern
                if value.startswith('{') and value.endswith('}'):
                    env_var = value[1:-1]
                    pool_data[key] = os.getenv(env_var, value)
        
        return pool_data
    
    def get_proxy(self) -> Optional[ProxyConfig]:
        """Get current proxy or rotate if needed"""
        if not self.enabled or not self.pools:
            return None
        
        # Initial selection
        if self.current_proxy is None:
            self.current_proxy = self._select_proxy()
            if self.current_proxy:
                logger.info(
                    f"Selected initial proxy: {self.current_proxy.name}",
                    step="proxy_manager",
                    event="proxy_selected"
                )
            return self.current_proxy
        
        # Check if rotation needed
        if self._should_rotate():
            old_proxy = self.current_proxy.name
            self.current_proxy = self._select_proxy()
            if self.current_proxy:
                logger.info(
                    f"Rotated proxy: {old_proxy} -> {self.current_proxy.name}",
                    step="proxy_manager",
                    event="proxy_rotated"
                )
        
        return self.current_proxy
    
    def _select_proxy(self) -> Optional[ProxyConfig]:
        """Select a proxy from the pool"""
        # Filter healthy proxies
        max_failures = self.health_check_config.get('max_failures', 3)
        healthy_proxies = [p for p in self.pools if p.failures < max_failures]
        
        if not healthy_proxies:
            logger.warning(
                "No healthy proxies available, resetting failure counts",
                step="proxy_manager",
                event="reset_failures"
            )
            # Reset all failure counts
            for p in self.pools:
                p.failures = 0
            healthy_proxies = self.pools
        
        if not healthy_proxies:
            logger.error(
                "No proxies available",
                step="proxy_manager",
                event="no_proxies"
            )
            return None
        
        # Select random proxy
        proxy = random.choice(healthy_proxies)
        
        # Perform health check if enabled
        if self.health_check_config.get('enabled', False):
            if not self.health_check(proxy):
                logger.warning(
                    f"Proxy {proxy.name} failed health check",
                    step="proxy_manager",
                    event="health_check_failed"
                )
                proxy.failures += 1
                # Try another proxy
                return self._select_proxy()
        
        proxy.last_used = time.time()
        return proxy
    
    def _should_rotate(self) -> bool:
        """Determine if proxy should be rotated"""
        if not self.current_proxy:
            return True
        
        if self.rotation_strategy == "per_session":
            # Only rotate on new session (manual reset)
            return False
        
        elif self.rotation_strategy == "per_application":
            return self.application_count >= self.apps_per_proxy
        
        elif self.rotation_strategy == "time_based":
            elapsed = time.time() - self.session_start_time
            return elapsed >= self.rotation_interval
        
        elif self.rotation_strategy == "per_candidate":
            # Handled externally
            return False
        
        return False
    
    def on_application_complete(self):
        """Track application count for rotation"""
        self.application_count += 1
        
        if self.rotation_strategy == "per_application" and self._should_rotate():
            self.application_count = 0
    
    def mark_proxy_failed(self):
        """Mark current proxy as failed"""
        if self.current_proxy:
            self.current_proxy.failures += 1
            logger.warning(
                f"Proxy {self.current_proxy.name} marked as failed (count: {self.current_proxy.failures})",
                step="proxy_manager",
                event="proxy_failed"
            )
    
    def health_check(self, proxy: ProxyConfig) -> bool:
        """Check if proxy is working"""
        if not self.health_check_config.get('enabled', False):
            return True
        
        try:
            url = self.health_check_config.get('url', 'https://lumtest.com/myip.json')
            timeout = self.health_check_config.get('timeout', 10)
            
            response = requests.get(
                url,
                proxies=proxy.get_proxy_dict(),
                timeout=timeout
            )
            
            if response.status_code == 200:
                logger.debug(
                    f"Proxy {proxy.name} health check passed",
                    step="proxy_manager",
                    event="health_check_pass"
                )
                return True
        
        except Exception as e:
            logger.debug(
                f"Proxy {proxy.name} health check failed: {e}",
                step="proxy_manager",
                event="health_check_fail"
            )
        
        return False
    
    def reset_session(self):
        """Reset session for new run"""
        self.application_count = 0
        self.session_start_time = time.time()
        
        if self.rotation_strategy in ["per_session", "per_candidate"]:
            self.current_proxy = None
    
    def get_stats(self) -> Dict:
        """Get proxy usage statistics"""
        return {
            'enabled': self.enabled,
            'current_proxy': self.current_proxy.name if self.current_proxy else None,
            'total_pools': len(self.pools),
            'healthy_pools': len([p for p in self.pools if p.failures < 3]),
            'application_count': self.application_count,
            'rotation_strategy': self.rotation_strategy
        }
