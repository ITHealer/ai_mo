# app/utils/logging_utils.py
"""
Structured logging utilities for content moderation.
"""
import logging
import threading
from datetime import datetime
from typing import Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class StructuredLogger:
    """
    Structured logger with worker context.
    """
    
    def __init__(self, name: str = "moderation"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Console handler with formatting
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] [%(worker)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _get_context(self, worker_name: Optional[str] = None) -> dict:
        """Get logging context"""
        if worker_name is None:
            worker_name = threading.current_thread().name
        
        return {
            'worker': worker_name,
            'timestamp': datetime.now().isoformat()
        }
    
    def info(self, message: str, worker_name: Optional[str] = None, **kwargs):
        """Log info message"""
        extra = self._get_context(worker_name)
        extra.update(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, worker_name: Optional[str] = None, **kwargs):
        """Log warning message"""
        extra = self._get_context(worker_name)
        extra.update(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, worker_name: Optional[str] = None, **kwargs):
        """Log error message"""
        extra = self._get_context(worker_name)
        extra.update(kwargs)
        self.logger.error(message, extra=extra)
    
    def debug(self, message: str, worker_name: Optional[str] = None, **kwargs):
        """Log debug message"""
        extra = self._get_context(worker_name)
        extra.update(kwargs)
        self.logger.debug(message, extra=extra)


# Global logger instance
structured_logger = StructuredLogger()