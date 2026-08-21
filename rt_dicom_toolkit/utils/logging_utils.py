"""
Logging utilities.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

def setup_logger(name, level=logging.INFO, log_file=None):
    """
    Configure and return a logger.
    
    Args:
        name: Logger name.
        level: Logging level.
        log_file: Optional log-file path.
        
    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to prevent duplicate output.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler.
    if log_file:
        # Ensure the destination directory exists.
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_log_filename(prefix, extension='log'):
    """
    Generate a timestamped log-file name.
    
    Args:
        prefix: File-name prefix.
        extension: File extension.
        
    Returns:
        Timestamped file name.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"

def add_file_handler(logger, log_file, level=logging.INFO):
    """
    Add a file handler to an existing logger.
    
    Args:
        logger: Logger instance.
        log_file: Log-file path.
        level: Logging level.
        
    Returns:
        Added file handler.
    """
    # Ensure the destination directory exists.
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return file_handler
