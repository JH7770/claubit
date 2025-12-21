"""
Centralized Logging Configuration

Provides unified logging setup for all modules with rotating file handlers,
separate error logging, and configurable console output.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional


# Global flag to prevent multiple setup calls
_logging_configured = False


def setup_logging(
    log_dir: str = "logs",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Configure global logging with rotation and multiple handlers.

    Sets up three handlers:
    1. Console handler (INFO+) - User-facing output
    2. File handler (DEBUG+) - Comprehensive logging
    3. Error handler (ERROR+) - Separate error log

    Args:
        log_dir: Directory for log files (default: "logs")
        console_level: Minimum level for console output (default: INFO)
        file_level: Minimum level for file output (default: DEBUG)
        max_bytes: Max file size before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    """
    global _logging_configured

    # Prevent duplicate configuration
    if _logging_configured:
        return

    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)

    # Define log file paths
    general_log_path = os.path.join(log_dir, "trading_bot.log")
    error_log_path = os.path.join(log_dir, "errors.log")

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels, handlers will filter

    # Remove any existing handlers (for safety)
    root_logger.handlers.clear()

    # 1. Console Handler (INFO+)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. File Handler (DEBUG+) - All logs
    file_handler = RotatingFileHandler(
        general_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # 3. Error Handler (ERROR+) - Separate error log
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger('ccxt').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('optuna').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)

    # Mark as configured
    _logging_configured = True

    # Log initialization
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Console: {logging.getLevelName(console_level)}, "
                f"File: {logging.getLevelName(file_level)}, "
                f"Max file size: {max_bytes / (1024*1024):.1f}MB")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for the specified module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance

    Example:
        from config.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Module initialized")
    """
    return logging.getLogger(name)


def set_module_level(module_name: str, level: int) -> None:
    """
    Set log level for a specific module.

    Useful for controlling verbosity of individual modules.

    Args:
        module_name: Name of the module
        level: Logging level (e.g., logging.DEBUG, logging.INFO)

    Example:
        set_module_level('modules.backtester', logging.WARNING)
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(level)


def disable_console_logging() -> None:
    """
    Disable console logging (file logging remains active).

    Useful for background processes or when running in non-interactive mode.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
            handler.setLevel(logging.CRITICAL + 1)  # Effectively disable


def enable_console_logging(level: int = logging.INFO) -> None:
    """
    Re-enable console logging.

    Args:
        level: Minimum level for console output
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
            handler.setLevel(level)


# Convenience function for backward compatibility
def configure_logging(*args, **kwargs):
    """Alias for setup_logging (backward compatibility)"""
    return setup_logging(*args, **kwargs)
