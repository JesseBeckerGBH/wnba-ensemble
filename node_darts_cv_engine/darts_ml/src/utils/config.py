"""Configuration management for the darts betting ensemble."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Config:
    """Configuration manager that loads and validates config.yaml."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to config.yaml. If None, uses default location.
        """
        if config_path is None:
            # Default to config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dots).
        
        Args:
            key: Configuration key (e.g., 'models.xgboost.n_estimators')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_path(self, key: str) -> Path:
        """
        Get path from configuration and resolve relative to project root.
        
        Args:
            key: Configuration key for path
            
        Returns:
            Resolved Path object
        """
        path_str = self.get(key)
        if path_str is None:
            raise ValueError(f"Path not found in config: {key}")
        
        path = Path(path_str)
        if not path.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent.parent.parent
            path = project_root / path
        
        return path
    
    @property
    def random_seed(self) -> int:
        """Get random seed for reproducibility."""
        return self.get('random_seed', 42)
    
    @property
    def data_raw_path(self) -> Path:
        """Get raw data directory path."""
        return self.get_path('paths.data_raw')
    
    @property
    def data_processed_path(self) -> Path:
        """Get processed data directory path."""
        return self.get_path('paths.data_processed')
    
    @property
    def models_path(self) -> Path:
        """Get models directory path."""
        return self.get_path('paths.models')
    
    @property
    def reports_path(self) -> Path:
        """Get reports directory path."""
        return self.get_path('paths.reports')


# Global config instance
_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Args:
        config_path: Path to config file (only used on first call)
        
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
