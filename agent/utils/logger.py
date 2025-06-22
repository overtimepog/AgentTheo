"""
Logging configuration for Browser Agent
Provides colored console output and file logging with real-time streaming
"""

import os
import sys
import logging
from colorlog import ColoredFormatter
from rich.console import Console
from rich.logging import RichHandler

# Rich console for pretty output
console = Console()

def setup_logging():
    """Setup logging configuration with color support"""
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    log_file = os.environ.get('LOG_FILE', None)
    
    # Create logger
    logger = logging.getLogger('browser-agent')
    logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = RichHandler(
        console=console,
        show_time=True,        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            # If file logging fails, just use console
            logger.warning(f"Could not create log file: {e}")
    
    # Log to stdout for Docker
    logger.propagate = False
    
    return logger

def get_logger(name=None):
    """Get a logger instance"""
    if name:
        return logging.getLogger(f'browser-agent.{name}')
    return logging.getLogger('browser-agent')