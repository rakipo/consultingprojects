"""Configuration management system."""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """Manages configuration loading and validation."""
    
    def __init__(self, config_dir: str = "config"):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir)
        self.engines_config = {}
        self.processing_config = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load all configuration files."""
        try:
            # Load engines configuration
            engines_path = self.config_dir / "engines.yaml"
            if engines_path.exists():
                with open(engines_path, 'r', encoding='utf-8') as f:
                    self.engines_config = yaml.safe_load(f)
            
            # Load processing configuration
            processing_path = self.config_dir / "processing.yaml"
            if processing_path.exists():
                with open(processing_path, 'r', encoding='utf-8') as f:
                    self.processing_config = yaml.safe_load(f)
                    
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._load_default_configs()
    
    def _load_default_configs(self):
        """Load default configurations if files are not found."""
        self.engines_config = {
            "engines": {
                "tesseract": {"enabled": True, "language": "tel"},
                "easyocr": {"enabled": True, "languages": ["te", "en"]}
            }
        }
        self.processing_config = {
            "preprocessing": {"resize_factor": 2.0},
            "output": {"formats": ["csv", "txt"]},
            "quality": {"minimum_confidence": 0.6}
        }
    
    def get_engine_config(self, engine_name: str) -> Dict[str, Any]:
        """Get configuration for a specific engine."""
        return self.engines_config.get("engines", {}).get(engine_name, {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.processing_config
    
    def is_engine_enabled(self, engine_name: str) -> bool:
        """Check if an engine is enabled."""
        engine_config = self.get_engine_config(engine_name)
        return engine_config.get("enabled", False)
    
    def get_enabled_engines(self) -> list:
        """Get list of enabled engines."""
        enabled = []
        for engine_name, config in self.engines_config.get("engines", {}).items():
            if config.get("enabled", False):
                enabled.append(engine_name)
        return enabled
    
    def resolve_env_variable(self, value: str) -> str:
        """Resolve environment variable if value starts with 'env:' (deprecated - now using direct values)."""
        if isinstance(value, str) and value.startswith("env:"):
            env_var = value[4:]  # Remove 'env:' prefix
            return os.getenv(env_var, "")
        return value