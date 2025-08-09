#!/usr/bin/env python3
"""
Path Configuration Utilities
Centralized path management for the PostgreSQL to Neo4j pipeline.
"""

import os
from pathlib import Path
from typing import Union, Optional


class ProjectPaths:
    """Centralized path configuration for the project."""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize project paths.
        
        Args:
            project_root: Optional project root directory. If None, auto-detects.
        """
        if project_root is None:
            # Auto-detect project root (directory containing this file's parent)
            self.project_root = Path(__file__).parent.parent.resolve()
        else:
            self.project_root = Path(project_root).resolve()
    
    # Directory paths
    @property
    def src_dir(self) -> Path:
        """Source code directory."""
        return self.project_root / "src"
    
    @property
    def tests_dir(self) -> Path:
        """Tests directory."""
        return self.project_root / "tests"
    
    @property
    def config_dir(self) -> Path:
        """Configuration files directory."""
        return self.project_root / "config"
    
    @property
    def scripts_dir(self) -> Path:
        """Utility scripts directory."""
        return self.project_root / "scripts"
    
    @property
    def output_dir(self) -> Path:
        """Output files directory."""
        return self.project_root / "output"
    
    @property
    def output_data_dir(self) -> Path:
        """Output data files directory."""
        return self.output_dir / "data"
    
    @property
    def output_metrics_dir(self) -> Path:
        """Output metrics directory."""
        return self.output_dir / "metrics"
    
    @property
    def output_logs_dir(self) -> Path:
        """Output logs directory."""
        return self.output_dir / "logs"
    
    @property
    def sql_dir(self) -> Path:
        """SQL and Cypher files directory."""
        return self.project_root / "sql"
    
    @property
    def docs_dir(self) -> Path:
        """Documentation directory."""
        return self.project_root / "docs"
    
    # Configuration file paths
    @property
    def config_boomer_load(self) -> Path:
        """Configuration file for data loading."""
        return self.config_dir / "config_boomer_load.yml"
    
    @property
    def config_boomer_model(self) -> Path:
        """Configuration file for model generation."""
        return self.config_dir / "config_boomer_model.yml"
    
    @property
    def config_boomer_temp(self) -> Path:
        """Temporary configuration file."""
        return self.config_dir / "config_boomer_temp.yml"
    
    @property
    def docker_compose_neo4j(self) -> Path:
        """Docker compose file for Neo4j."""
        return self.config_dir / "docker-compose-neo4j-mcp.yml"
    
    @property
    def environment_yml(self) -> Path:
        """Main environment configuration."""
        return self.config_dir / "environment.yml"
    
    # Source file paths
    @property
    def postgres_query_runner(self) -> Path:
        """PostgreSQL query runner module."""
        return self.src_dir / "postgres_query_runner.py"
    
    @property
    def neo4j_model_generator(self) -> Path:
        """Neo4j model generator module."""
        return self.src_dir / "neo4j_model_generator.py"
    
    @property
    def neo4j_data_loader(self) -> Path:
        """Neo4j data loader module."""
        return self.src_dir / "neo4j_data_loader.py"
    
    def ensure_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            self.src_dir,
            self.tests_dir,
            self.config_dir,
            self.scripts_dir,
            self.output_dir,
            self.output_data_dir,
            self.output_metrics_dir,
            self.output_logs_dir,
            self.sql_dir,
            self.docs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_output_file_path(self, filename: str, output_type: str = "data") -> Path:
        """
        Get a path for an output file in the appropriate subdirectory.
        
        Args:
            filename: Name of the output file
            output_type: Type of output ("data", "metrics", "logs")
            
        Returns:
            Path object for the output file
        """
        if output_type == "data":
            return self.output_data_dir / filename
        elif output_type == "metrics":
            return self.output_metrics_dir / filename
        elif output_type == "logs":
            return self.output_logs_dir / filename
        else:
            return self.output_dir / filename
    
    def get_timestamped_filename(self, base_name: str, extension: str, 
                                output_type: str = "data") -> Path:
        """
        Generate a timestamped filename in the appropriate output directory.
        
        Args:
            base_name: Base name for the file (e.g., "neo4j_model")
            extension: File extension (e.g., "json", "txt")
            output_type: Type of output ("data", "metrics", "logs")
            
        Returns:
            Path object with timestamped filename
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.{extension}"
        return self.get_output_file_path(filename, output_type)
    
    def resolve_config_path(self, config_name: str) -> Path:
        """
        Resolve a configuration file path by name.
        
        Args:
            config_name: Name of the configuration (e.g., "load", "model", "temp")
            
        Returns:
            Path to the configuration file
        """
        config_mapping = {
            "load": self.config_boomer_load,
            "model": self.config_boomer_model,
            "temp": self.config_boomer_temp
        }
        
        if config_name in config_mapping:
            return config_mapping[config_name]
        else:
            # Assume it's a direct filename in config directory
            return self.config_dir / config_name
    
    def __str__(self) -> str:
        """String representation of project paths."""
        return f"ProjectPaths(root={self.project_root})"
    
    def __repr__(self) -> str:
        """Detailed representation of project paths."""
        return f"ProjectPaths(project_root='{self.project_root}')"


# Global instance for easy access
paths = ProjectPaths()


def ensure_output_directory(file_path: Union[str, Path]) -> Path:
    """
    Ensure the directory for a file path exists.
    
    Args:
        file_path: Path to a file
        
    Returns:
        Path object with directory created
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return paths.project_root


def get_config_path(config_name: str) -> Path:
    """
    Get path to a configuration file.
    
    Args:
        config_name: Name of configuration ("load", "model", "temp") or filename
        
    Returns:
        Path to configuration file
    """
    return paths.resolve_config_path(config_name)


def get_output_path(filename: str, output_type: str = "data") -> Path:
    """
    Get path for an output file.
    
    Args:
        filename: Name of the output file
        output_type: Type of output ("data", "metrics", "logs")
        
    Returns:
        Path to output file with directory created
    """
    output_path = paths.get_output_file_path(filename, output_type)
    ensure_output_directory(output_path)
    return output_path


def get_timestamped_output_path(base_name: str, extension: str, 
                               output_type: str = "data") -> Path:
    """
    Get timestamped output file path.
    
    Args:
        base_name: Base name for the file
        extension: File extension
        output_type: Type of output ("data", "metrics", "logs")
        
    Returns:
        Path to timestamped output file with directory created
    """
    output_path = paths.get_timestamped_filename(base_name, extension, output_type)
    ensure_output_directory(output_path)
    return output_path


if __name__ == "__main__":
    # Demo usage
    print("Project Paths Demo")
    print("=" * 50)
    print(f"Project root: {paths.project_root}")
    print(f"Source directory: {paths.src_dir}")
    print(f"Config directory: {paths.config_dir}")
    print(f"Output data directory: {paths.output_data_dir}")
    print(f"Output metrics directory: {paths.output_metrics_dir}")
    print()
    
    print("Configuration paths:")
    print(f"Load config: {paths.config_boomer_load}")
    print(f"Model config: {paths.config_boomer_model}")
    print()
    
    print("Utility functions:")
    print(f"Config path (load): {get_config_path('load')}")
    print(f"Output path (data): {get_output_path('test.csv', 'data')}")
    print(f"Timestamped path: {get_timestamped_output_path('model', 'json', 'data')}")
    print()
    
    print("Ensuring directories exist...")
    paths.ensure_directories()
    print("✅ All directories created/verified")