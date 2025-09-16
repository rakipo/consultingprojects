"""
Logging configuration module for GraphRAG Retrieval Agent.

This module provides structured logging setup with JSON format, external volume storage,
and execution tracing capabilities. It loads configuration from YAML files and provides
utilities for logging throughout the application.
"""

import logging
import logging.config
import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from datetime import datetime

from .exceptions import ConfigurationError, ErrorCodes


class ExecutionTracer:
    """Handles execution tracing with unique request IDs and timing."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.traces: Dict[str, Dict[str, Any]] = {}
    
    def start_trace(self, operation: str, details: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new execution trace.
        
        Args:
            operation: Name of the operation being traced
            details: Optional additional details about the operation
            
        Returns:
            Unique request ID for this trace
        """
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        trace_data = {
            "request_id": request_id,
            "operation": operation,
            "start_time": start_time,
            "start_timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
            "status": "started"
        }
        
        self.traces[request_id] = trace_data
        
        self.logger.info(
            "Execution trace started",
            extra={
                "request_id": request_id,
                "operation": operation,
                "trace_event": "start",
                "details": details or {}
            }
        )
        
        return request_id
    
    def end_trace(self, request_id: str, status: str = "completed", 
                  result: Optional[Dict[str, Any]] = None, 
                  error: Optional[Exception] = None) -> None:
        """
        End an execution trace.
        
        Args:
            request_id: The request ID returned by start_trace
            status: Status of the operation (completed, failed, etc.)
            result: Optional result data
            error: Optional exception if the operation failed
        """
        if request_id not in self.traces:
            self.logger.warning(f"Attempt to end unknown trace: {request_id}")
            return
        
        trace_data = self.traces[request_id]
        end_time = time.time()
        execution_time = end_time - trace_data["start_time"]
        
        trace_data.update({
            "end_time": end_time,
            "end_timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": execution_time,
            "status": status,
            "result": result,
            "error": str(error) if error else None
        })
        
        log_level = logging.ERROR if status == "failed" else logging.INFO
        self.logger.log(
            log_level,
            f"Execution trace {status}",
            extra={
                "request_id": request_id,
                "operation": trace_data["operation"],
                "trace_event": "end",
                "execution_time_seconds": execution_time,
                "status": status,
                "result": result,
                "error": str(error) if error else None
            }
        )
        
        # Clean up completed traces to prevent memory leaks
        del self.traces[request_id]
    
    def log_trace_event(self, request_id: str, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an intermediate event in an execution trace.
        
        Args:
            request_id: The request ID for the trace
            event: Name of the event
            details: Optional event details
        """
        if request_id not in self.traces:
            self.logger.warning(f"Attempt to log event for unknown trace: {request_id}")
            return
        
        trace_data = self.traces[request_id]
        
        self.logger.info(
            f"Trace event: {event}",
            extra={
                "request_id": request_id,
                "operation": trace_data["operation"],
                "trace_event": event,
                "details": details or {}
            }
        )


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        if hasattr(record, 'operation'):
            log_data["operation"] = record.operation
        if hasattr(record, 'trace_event'):
            log_data["trace_event"] = record.trace_event
        if hasattr(record, 'execution_time_seconds'):
            log_data["execution_time_seconds"] = record.execution_time_seconds
        if hasattr(record, 'status'):
            log_data["status"] = record.status
        if hasattr(record, 'result'):
            log_data["result"] = record.result
        if hasattr(record, 'error'):
            log_data["error"] = record.error
        if hasattr(record, 'details'):
            log_data["details"] = record.details
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def setup_logging(config_path: str = "config/logging.yaml") -> None:
    """
    Set up logging configuration from YAML file.
    
    Args:
        config_path: Path to the logging configuration YAML file
        
    Raises:
        ConfigurationError: If the configuration file cannot be loaded or is invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigurationError(
            ErrorCodes.CONFIG_FILE_NOT_FOUND,
            f"Logging configuration file not found: {config_path}",
            {"config_path": config_path}
        )
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            ErrorCodes.CONFIG_INVALID_FORMAT,
            f"Invalid YAML format in logging configuration: {e}",
            {"config_path": config_path, "yaml_error": str(e)}
        )
    except Exception as e:
        raise ConfigurationError(
            ErrorCodes.CONFIG_FILE_NOT_FOUND,
            f"Failed to read logging configuration file: {e}",
            {"config_path": config_path, "error": str(e)}
        )
    
    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Add custom JSON formatter to the configuration
    if 'formatters' not in config:
        config['formatters'] = {}
    
    config['formatters']['json_custom'] = {
        '()': 'modules.logging_config.JSONFormatter',
        'datefmt': '%Y-%m-%d %H:%M:%S'
    }
    
    try:
        logging.config.dictConfig(config)
    except Exception as e:
        raise ConfigurationError(
            ErrorCodes.CONFIG_VALIDATION_FAILED,
            f"Failed to configure logging: {e}",
            {"config_path": config_path, "error": str(e)}
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def get_execution_tracer(logger_name: str = "graphrag.execution") -> ExecutionTracer:
    """
    Get an execution tracer instance.
    
    Args:
        logger_name: Name of the logger to use for tracing
        
    Returns:
        ExecutionTracer instance
    """
    logger = get_logger(logger_name)
    return ExecutionTracer(logger)


def log_exception(logger: logging.Logger, exception: Exception, 
                  context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception with structured context information.
    
    Args:
        logger: Logger instance to use
        exception: Exception to log
        context: Optional context information
    """
    error_data = {
        "exception_type": type(exception).__name__,
        "exception_message": str(exception),
        "context": context or {}
    }
    
    # Add error code if it's a GraphRAG exception
    if hasattr(exception, 'code'):
        error_data["error_code"] = exception.code
    if hasattr(exception, 'details'):
        error_data["error_details"] = exception.details
    
    logger.error(
        f"Exception occurred: {exception}",
        extra=error_data,
        exc_info=True
    )


# Global execution tracer instance
_global_tracer: Optional[ExecutionTracer] = None


def get_global_tracer() -> ExecutionTracer:
    """Get the global execution tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = get_execution_tracer()
    return _global_tracer


def initialize_logging() -> None:
    """Initialize logging system with default configuration."""
    try:
        setup_logging()
        logger = get_logger("graphrag.logging")
        logger.info("Logging system initialized successfully")
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger("graphrag.logging")
        logger.error(f"Failed to initialize logging from config, using fallback: {e}")