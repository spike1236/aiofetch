"""
aiofetch - Asynchronous web scraping and file handling toolkit
"""

from .utils import (
    PathHandler,
    FileIO,
    MetadataExtractor,
    MetadataManager,
    ContentParser
)

from .downloader import AsyncDownloader
from .crawler import (
    BaseCrawler,
    BatchProcessor,
    RateLimiter
)
from .logger import (
    LoggerFactory,
    ErrorTracker,
    ProgressTracker
)

__all__ = [
    # Core utilities
    'PathHandler',
    'FileIO',
    'MetadataExtractor',
    'MetadataManager',
    'ContentParser',

    # Downloaders and crawlers
    'AsyncDownloader',
    'BaseCrawler',
    'BatchProcessor',
    'RateLimiter',

    # Logging and error tracking
    'LoggerFactory',
    'ErrorTracker',
    'ProgressTracker'
]
