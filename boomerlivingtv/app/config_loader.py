#!/usr/bin/env python3
"""
Configuration Loader
Loads and manages configuration from YAML files and environment variables
"""

import os
import yaml
import logging
from typing import Any, Dict, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigLoader:
    def __init__(self, env_config_path: str = "env_config.yaml", param_config_path: str = "param_config.yaml"):
        """Initialize configuration loader"""
        self.env_config_path = env_config_path
        self.param_config_path = param_config_path
        self.env_config = {}
        self.param_config = {}
        self.resolved_config = {}
        
        self.load_configurations()
    
    def load_configurations(self):
        """Load all configuration files"""
        try:
            # Load environment configuration
            if os.path.exists(self.env_config_path):
                with open(self.env_config_path, 'r') as file:
                    self.env_config = yaml.safe_load(file) or {}
                logger.info(f"Loaded environment config from {self.env_config_path}")
            else:
                logger.warning(f"Environment config file not found: {self.env_config_path}")
            
            # Load parameters configuration
            if os.path.exists(self.param_config_path):
                with open(self.param_config_path, 'r') as file:
                    self.param_config = yaml.safe_load(file) or {}
                logger.info(f"Loaded parameters config from {self.param_config_path}")
            else:
                logger.warning(f"Parameters config file not found: {self.param_config_path}")
            
            # Resolve environment variables
            self.resolved_config = self._resolve_environment_variables()
            
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration files: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def _resolve_environment_variables(self) -> Dict[str, Any]:
        """Resolve environment variables from configuration"""
        resolved = {}
        
        def resolve_section(section_data: Dict[str, Any], section_name: str = "") -> Dict[str, Any]:
            resolved_section = {}
            
            for key, value in section_data.items():
                if isinstance(value, dict):
                    if 'env_var' in value:
                        # This is an environment variable configuration
                        env_var = value['env_var']
                        default = value.get('default')
                        var_type = value.get('type', 'str')
                        
                        # Get value from environment or use default
                        env_value = os.getenv(env_var, default)
                        
                        # Convert type if specified
                        resolved_section[key] = self._convert_type(env_value, var_type)
                        
                        # Log sensitive variables without showing value
                        if value.get('sensitive', False):
                            logger.info(f"Loaded {section_name}.{key} from {env_var} (sensitive)")
                        else:
                            logger.debug(f"Loaded {section_name}.{key} = {resolved_section[key]} from {env_var}")
                    else:
                        # Nested section
                        nested_name = f"{section_name}.{key}" if section_name else key
                        resolved_section[key] = resolve_section(value, nested_name)
                else:
                    # Direct value
                    resolved_section[key] = value
            
            return resolved_section
        
        return resolve_section(self.env_config)
    
    def _convert_type(self, value: Any, var_type: str) -> Any:
        """Convert string value to specified type"""
        if value is None:
            return None
        
        try:
            if var_type == 'int':
                return int(value)
            elif var_type == 'float':
                return float(value)
            elif var_type == 'bool':
                if isinstance(value, bool):
                    return value
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif var_type == 'list':
                if isinstance(value, list):
                    return value
                return [item.strip() for item in str(value).split(',')]
            else:  # str or default
                return str(value)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert {value} to {var_type}: {e}")
            return value
    
    def get_env_config(self, path: str, default: Any = None) -> Any:
        """Get environment configuration value by dot-separated path"""
        return self._get_nested_value(self.resolved_config, path, default)
    
    def get_param_config(self, path: str, default: Any = None) -> Any:
        """Get parameter configuration value by dot-separated path"""
        return self._get_nested_value(self.param_config, path, default)
    
    def _get_nested_value(self, data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get nested dictionary value by dot-separated path"""
        keys = path.split('.')
        current = data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def get_database_config(self, db_type: str) -> Dict[str, Any]:
        """Get database configuration for specified type"""
        return self.get_env_config(f'database.{db_type}', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.get_env_config('server', {})
    
    def get_cypher_config(self) -> Dict[str, Any]:
        """Get Cypher configuration"""
        return self.get_env_config('cypher', {})
    
    def get_migration_config(self) -> Dict[str, Any]:
        """Get migration configuration"""
        return self.get_env_config('migration', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get_env_config('performance', {})
    
    def get_query_template(self, category: str, query_name: str) -> str:
        """Get query template"""
        return self.get_param_config(f'{category}.{query_name}', '')
    
    def get_database_queries(self, db_type: str) -> Dict[str, str]:
        """Get database queries for specified type"""
        return self.get_param_config(f'database_queries.{db_type}', {})
    
    def get_migration_templates(self) -> Dict[str, str]:
        """Get migration templates"""
        return self.get_param_config('migration_templates', {})
    
    def get_sample_queries(self, category: str) -> Dict[str, str]:
        """Get sample queries for specified category"""
        return self.get_param_config(f'sample_queries.{category}', {})
    
    def get_analytics_templates(self) -> Dict[str, str]:
        """Get analytics query templates"""
        return self.get_param_config('analytics_templates', {})
    
    def get_mcp_server_config(self) -> Dict[str, Any]:
        """Get MCP server configuration"""
        return self.get_param_config('mcp_server', {})
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default values and constants"""
        return self.get_param_config('defaults', {})
    
    def get_message(self, category: str, message_key: str, **kwargs) -> str:
        """Get formatted message"""
        message_template = self.get_param_config(f'defaults.messages.{category}.{message_key}', '')
        if message_template and kwargs:
            try:
                return message_template.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing format key {e} for message {category}.{message_key}")
                return message_template
        return message_template
    
    def substitute_template(self, template: str, **kwargs) -> str:
        """Substitute variables in template"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.warning(f"Missing template variable: {e}")
            return template
    
    def validate_config(self) -> bool:
        """Validate configuration completeness"""
        required_sections = [
            'database.postgres',
            'database.neo4j',
            'server',
        ]
        
        missing_sections = []
        for section in required_sections:
            if not self.get_env_config(section):
                missing_sections.append(section)
        
        if missing_sections:
            logger.error(f"Missing required configuration sections: {missing_sections}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def get_sensitive_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary without sensitive values"""
        def mask_sensitive(data: Dict[str, Any], path: str = "") -> Dict[str, Any]:
            masked = {}
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict):
                    if value.get('sensitive', False):
                        masked[key] = "***MASKED***"
                    else:
                        masked[key] = mask_sensitive(value, current_path)
                else:
                    masked[key] = value
            
            return masked
        
        return {
            'env_config': mask_sensitive(self.resolved_config),
            'param_config_keys': list(self.param_config.keys()),
            'config_files': {
                'env_config_path': self.env_config_path,
                'param_config_path': self.param_config_path,
                'env_config_exists': os.path.exists(self.env_config_path),
                'param_config_exists': os.path.exists(self.param_config_path)
            }
        }

# Global configuration instance
_config_instance: Optional[ConfigLoader] = None

def get_config(env_config_path: str = "env_config.yaml", param_config_path: str = "param_config.yaml") -> ConfigLoader:
    """Get global configuration instance"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = ConfigLoader(env_config_path, param_config_path)
    
    return _config_instance

def reload_config(env_config_path: str = "env_config.yaml", param_config_path: str = "param_config.yaml") -> ConfigLoader:
    """Reload configuration"""
    global _config_instance
    _config_instance = ConfigLoader(env_config_path, param_config_path)
    return _config_instance

# Example usage and testing
if __name__ == "__main__":
    # Test configuration loading
    config = ConfigLoader()
    
    print("Configuration Summary:")
    print(yaml.dump(config.get_sensitive_config_summary(), default_flow_style=False))
    
    print("\nDatabase Configs:")
    print(f"PostgreSQL: {config.get_database_config('postgres')}")
    print(f"Neo4j: {config.get_database_config('neo4j')}")
    
    print("\nSample Query:")
    query = config.get_query_template('sample_queries.analysis', 'productive_authors')
    print(query)
    
    print("\nMessage Example:")
    message = config.get_message('success', 'migration_complete')
    print(message)