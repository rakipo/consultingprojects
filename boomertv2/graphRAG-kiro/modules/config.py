"""
Configuration management module for GraphRAG Retrieval Agent.

This module provides functionality to load and validate YAML configuration files
for the application, including Neo4j connection settings, embedding model
configuration, and other system parameters.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .exceptions import ConfigurationError, ErrorCodes
from .logging_config import get_logger, log_exception


def load_config(config_path: str = "config/app.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        ConfigurationError: If configuration cannot be loaded or is invalid
    """
    logger = get_logger("graphrag.config")
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigurationError(
            ErrorCodes.CONFIG_FILE_NOT_FOUND,
            f"Configuration file not found: {config_path}",
            {"config_path": config_path}
        )
    
    try:
        logger.info(f"Loading configuration from {config_path}")
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ConfigurationError(
                ErrorCodes.CONFIG_INVALID_FORMAT,
                "Configuration file must contain a YAML dictionary",
                {"config_path": config_path, "config_type": type(config).__name__}
            )
        
        # Override with environment variables if present
        config = _apply_environment_overrides(config)
        
        # Validate configuration
        validate_config(config)
        
        logger.info("Configuration loaded successfully")
        return config
        
    except yaml.YAMLError as e:
        error = ConfigurationError(
            ErrorCodes.CONFIG_INVALID_FORMAT,
            f"Invalid YAML format in configuration file: {e}",
            {"config_path": config_path, "yaml_error": str(e)}
        )
        log_exception(logger, error)
        raise error
        
    except ConfigurationError:
        # Re-raise configuration errors as-is
        raise
        
    except Exception as e:
        error = ConfigurationError(
            ErrorCodes.CONFIG_FILE_NOT_FOUND,
            f"Failed to load configuration file: {e}",
            {"config_path": config_path, "error": str(e)}
        )
        log_exception(logger, error)
        raise error


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and required fields.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigurationError: If configuration is invalid
    """
    logger = get_logger("graphrag.config")
    
    try:
        # Check for required sections
        required_sections = ["neo4j", "embedding"]
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
        
        if missing_sections:
            raise ConfigurationError(
                ErrorCodes.CONFIG_MISSING_REQUIRED,
                f"Missing required configuration sections: {missing_sections}",
                {"missing_sections": missing_sections, "required_sections": required_sections}
            )
        
        # Validate Neo4j configuration
        neo4j_config = config["neo4j"]
        required_neo4j_fields = ["uri", "username", "password"]
        missing_neo4j_fields = []
        
        for field in required_neo4j_fields:
            if field not in neo4j_config or not neo4j_config[field]:
                missing_neo4j_fields.append(field)
        
        if missing_neo4j_fields:
            raise ConfigurationError(
                ErrorCodes.CONFIG_MISSING_REQUIRED,
                f"Missing required Neo4j configuration fields: {missing_neo4j_fields}",
                {"missing_fields": missing_neo4j_fields, "section": "neo4j"}
            )
        
        # Validate embedding configuration
        embedding_config = config["embedding"]
        if "model_name" not in embedding_config:
            logger.warning("No embedding model specified, using default: all-MiniLM-L6-v2")
            embedding_config["model_name"] = "all-MiniLM-L6-v2"
        
        # Set defaults for optional fields
        if "database" not in neo4j_config:
            neo4j_config["database"] = "neo4j"
        
        logger.debug("Configuration validation completed successfully")
        
    except ConfigurationError:
        # Re-raise configuration errors as-is
        raise
        
    except Exception as e:
        error = ConfigurationError(
            ErrorCodes.CONFIG_VALIDATION_FAILED,
            f"Configuration validation failed: {e}",
            {"error": str(e), "error_type": type(e).__name__}
        )
        log_exception(logger, error)
        raise error


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration values.
    
    Returns:
        Dictionary containing default configuration
    """
    return {
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password",
            "database": "neo4j"
        },
        "embedding": {
            "model_name": "all-MiniLM-L6-v2"
        },
        "retrieval": {
            "default_limit": 5,
            "max_limit": 20,
            "default_expand_graph": True
        },
        "mcp": {
            "server_name": "graphrag-retrieval-agent",
            "tools": ["graph_retrieve"]
        }
    }


def create_default_config_file(config_path: str = "config/app.yaml") -> None:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path where to create the configuration file
    """
    logger = get_logger("graphrag.config")
    config_file = Path(config_path)
    
    # Create config directory if it doesn't exist
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    if config_file.exists():
        logger.warning(f"Configuration file already exists: {config_path}")
        return
    
    try:
        default_config = get_default_config()
        
        with open(config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created default configuration file: {config_path}")
        
    except Exception as e:
        error = ConfigurationError(
            ErrorCodes.CONFIG_FILE_NOT_FOUND,
            f"Failed to create default configuration file: {e}",
            {"config_path": config_path, "error": str(e)}
        )
        log_exception(logger, error)
        raise error


def _apply_environment_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Args:
        config: Base configuration dictionary
        
    Returns:
        Configuration with environment overrides applied
    """
    # Neo4j environment variables
    if os.getenv("NEO4J_URI"):
        config.setdefault("neo4j", {})["uri"] = os.getenv("NEO4J_URI")
    
    if os.getenv("NEO4J_USERNAME"):
        config.setdefault("neo4j", {})["username"] = os.getenv("NEO4J_USERNAME")
    
    if os.getenv("NEO4J_PASSWORD"):
        config.setdefault("neo4j", {})["password"] = os.getenv("NEO4J_PASSWORD")
    
    if os.getenv("NEO4J_DATABASE"):
        config.setdefault("neo4j", {})["database"] = os.getenv("NEO4J_DATABASE")
    
    # Embedding model override
    if os.getenv("EMBEDDING_MODEL"):
        config.setdefault("embedding", {})["model_name"] = os.getenv("EMBEDDING_MODEL")
    
    # Logging level override
    if os.getenv("LOG_LEVEL"):
        config.setdefault("logging", {})["level"] = os.getenv("LOG_LEVEL")
    
    return config