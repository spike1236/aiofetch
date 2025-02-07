import logging
import os
from datetime import datetime
import json
from collections import defaultdict
from typing import Optional, Dict, Any, List


class LogConfig:
    """Logging configuration constants"""
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    CONSOLE_FORMAT = '%(message)s'
    DATE_FORMAT = '%Y%m%d_%H%M%S'
    LOG_DIR = 'logs'


class LoggerFactory:
    _loggers = set()

    @staticmethod
    def create_logger(name: str, log_dir: str = LogConfig.LOG_DIR, console: bool = False,
                      file_prefix: Optional[str] = None,
                      level: int = logging.INFO) -> logging.Logger:
        logger = logging.getLogger(name)

        if name not in LoggerFactory._loggers:
            logger.setLevel(level)

            os.makedirs(log_dir, exist_ok=True)

            timestamp = datetime.now().strftime(LogConfig.DATE_FORMAT)
            prefix = f"{file_prefix}_" if file_prefix else ""
            log_file = os.path.join(log_dir, f"{prefix}{timestamp}_{name}.log")

            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setFormatter(logging.Formatter(LogConfig.DEFAULT_FORMAT))
            logger.addHandler(fh)

            if console:
                ch = logging.StreamHandler()
                ch.setFormatter(logging.Formatter(LogConfig.CONSOLE_FORMAT))
                logger.addHandler(ch)

            LoggerFactory._loggers.add(name)

        return logger


class ProgressTracker:
    """Track progress of long-running operations"""
    def __init__(self, logger: logging.Logger, total: int, update_frequency: int = 100):
        self.logger = logger
        self.total = total
        self.current = 0
        self.frequency = update_frequency
        self.start_time = datetime.now()
        self.milestones: Dict[str, datetime] = {}

    def update(self, increment: int = 1, message: Optional[str] = None):
        """Update progress counter"""
        if increment < 0:
            raise ValueError("Increment must be a non-negative integer")

        self.current += increment
        if increment == 0 or self.current % self.frequency == 0 or self.current == self.total:
            self._log_progress(message)

    def add_milestone(self, name: str):
        """Mark a milestone with current timestamp"""
        self.milestones[name] = datetime.now()

    def _log_progress(self, message: Optional[str] = None):
        """Log current progress with rate and ETA"""
        elapsed = max(0.001, (datetime.now() - self.start_time).total_seconds())
        rate = self.current / elapsed

        progress = (self.current / self.total) * 100
        eta = (self.total - self.current) / max(0.001, rate)

        status = (
            f"Progress: {self.current}/{self.total} ({progress:.1f}%) "
            f"Rate: {rate:.1f} items/sec ETA: {eta:.0f}s"
        )

        if message:
            status = f"{status} - {message}"

        self.logger.info(status)


class ErrorTracker:
    """Track and analyze errors during execution"""
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.errors: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.counts: Dict[str, int] = defaultdict(int)

    def log_error(self, error_type: str, message: str,
                  details: Optional[Dict[str, Any]] = None):
        """Log an error with optional details"""
        self.errors[error_type].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'details': details
        })
        self.counts[error_type] += 1

        self.logger.error(f"{error_type}: {message}")
        if details:
            self.logger.debug(f"Details: {json.dumps(details, indent=2)}")

    def log_exception(self, error_type: str, exception: Exception,
                      details: Optional[Dict[str, Any]] = None):
        """Log an exception with optional details"""
        self.log_error(error_type, str(exception), details)

    def get_summary(self) -> Dict[str, Any]:
        """Get error summary"""
        return {
            'total_errors': sum(self.counts.values()),
            'by_type': dict(self.counts),
            'error_log': dict(self.errors)
        }
