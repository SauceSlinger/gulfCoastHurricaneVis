"""
Logging configuration for Gulf Coast Hurricane Visualization Dashboard.

This module provides centralized logging configuration with different levels
for development, production, and debugging scenarios.
"""

import logging
import os
from pathlib import Path
from datetime import datetime

class DashboardLogger:
    """Centralized logging configuration for the hurricane dashboard."""
    
    def __init__(self, name: str = "hurricane_dashboard", level: str = "INFO"):
        """
        Initialize the dashboard logger.
        
        Args:
            name: Logger name (typically __name__ of the calling module)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Avoid duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers for logging."""
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # File handler for persistent logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"dashboard_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_format = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        return self.logger

def get_logger(name: str = "hurricane_dashboard", level: str = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name
        level: Override default logging level
        
    Returns:
        Configured logger instance
    """
    # Check environment variable for logging level
    if level is None:
        level = os.getenv('HURRICANE_LOG_LEVEL', 'INFO')
    
    dashboard_logger = DashboardLogger(name, level)
    return dashboard_logger.get_logger()

# Convenience function for common logging operations
def log_performance(logger: logging.Logger, operation: str, duration: float):
    """Log performance metrics in a standardized format."""
    if duration > 1.0:
        logger.warning(f"⚠️ Slow operation: {operation} took {duration:.2f}s")
    else:
        logger.debug(f"⚡ {operation} completed in {duration:.3f}s")

def log_data_operation(logger: logging.Logger, operation: str, record_count: int):
    """Log data processing operations."""
    logger.info(f"📊 {operation}: {record_count:,} records processed")

def log_error_with_context(logger: logging.Logger, operation: str, error: Exception):
    """Log errors with operation context."""
    logger.error(f"❌ {operation} failed: {str(error)}", exc_info=True)