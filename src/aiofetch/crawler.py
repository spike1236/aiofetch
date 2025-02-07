import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
from typing import Optional, Set, List, Any, Callable, Awaitable
from .logger import LoggerFactory, ErrorTracker, ProgressTracker


class BaseCrawler:
    """Base class for web crawlers with common functionality"""
    def __init__(self, base_url: str, concurrent_limit: int = 10, timeout: int = 30):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls: Set[str] = set()
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        self.logger = LoggerFactory.create_logger(
            self.__class__.__name__,
            file_prefix='crawler'
        )
        self.error_tracker = ErrorTracker(self.logger)
        self.session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> 'BaseCrawler':
        """Initialize crawler session"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self

    async def stop(self) -> None:
        """Cleanup crawler session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> 'BaseCrawler':
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop()

    async def fetch_page(self, url: str, retries: int = 3,
                         delay: float = 1) -> Optional[str]:
        """Fetch page content with retry logic"""
        if not self.session:
            raise RuntimeError("Crawler session not initialized. \
                               Use 'async with' or await start()")

        for attempt in range(retries):
            try:
                async with self.semaphore:
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.text()

                        self.error_tracker.log_error(
                            'http_error',
                            f"Status {response.status} for {url}",
                            {'attempt': attempt + 1}
                        )

                        if response.status == 404:
                            break

            except aiohttp.ClientError as e:
                self.error_tracker.log_error(
                    'network_error',
                    str(e),
                    {'url': url, 'attempt': attempt + 1}
                )
            except Exception as e:
                self.error_tracker.log_error(
                    'unexpected_error',
                    str(e),
                    {'url': url, 'attempt': attempt + 1}
                )

            if attempt < retries - 1:
                await asyncio.sleep(delay + (attempt + 1))

        return None

    async def parse_html(self, html: str,
                         url: Optional[str] = None) -> Optional[BeautifulSoup]:
        """Parse HTML content using BeautifulSoup"""
        if not html:
            return None
        return BeautifulSoup(html, 'html.parser')

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to target domain"""
        return url.startswith(self.base_url)

    def normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """Normalize URL using base URL"""
        return urljoin(base_url or self.base_url, url)

    def extract_relative_path(self, url: str) -> str:
        """Extract relative path from URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        return path if path else ''


class BatchProcessor:
    """Helper class for processing items in batches"""
    def __init__(self, batch_size: int = 10, delay: float = 3,
                 logger: Optional[LoggerFactory] = None):
        self.batch_size = batch_size
        self.delay = delay
        self.queue = asyncio.Queue()
        self.logger = logger or LoggerFactory.create_logger('BatchProcessor')
        self.progress: Optional[ProgressTracker] = None

    async def add_items(self, items: List[Any]) -> None:
        """Add multiple items to queue"""
        for item in items:
            await self.queue.put(item)

        self.progress = ProgressTracker(
            self.logger,
            self.queue.qsize(),
            update_frequency=self.batch_size
        )

    async def process_batches(self, processor_func: Callable[[List[Any]],
                                                             Awaitable[None]]):
        """Process items in batches with progress tracking"""
        try:
            while True:
                batch = []
                try:
                    for _ in range(self.batch_size):
                        if self.queue.empty():
                            break
                        item = await self.queue.get()
                        batch.append(item)

                    if not batch:
                        break

                    await processor_func(batch)

                    if self.progress:
                        self.progress.update(len(batch))

                    for _ in batch:
                        self.queue.task_done()

                    await asyncio.sleep(self.delay)

                except Exception as e:
                    self.logger.error(f"Batch processing error: {str(e)}")
                    for item in batch:
                        await self.queue.put(item)

        except asyncio.CancelledError:
            for item in batch:
                await self.queue.put(item)
            raise


class RateLimiter:
    """Rate limiter for controlling request frequency"""
    def __init__(self, requests_per_second: float = 1, timeout: float = 60):
        self.delay = 1.0 / requests_per_second
        self.last_request = 0
        self._session_usage_count = 0
        self._lock = asyncio.Lock()
        self.timeout = timeout

    async def acquire(self) -> None:
        """Wait until rate limit allows next request"""
        try:
            async with asyncio.timeout(self.timeout):
                async with self._lock:
                    now = datetime.now().timestamp()
                    elapsed = now - self.last_request
                    if elapsed < self.delay:
                        await asyncio.sleep(self.delay - elapsed)
                    self.last_request = datetime.now().timestamp()
        except asyncio.TimeoutError:
            raise TimeoutError("Rate limiter timeout exceeded")

    async def __aenter__(self) -> 'RateLimiter':
        await self.acquire()
        self._session_usage_count += 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._session_usage_count -= 1
