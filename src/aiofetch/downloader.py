import aiohttp
import aiofiles
import asyncio
import os
from aiofiles.os import makedirs
from datetime import datetime
from typing import List, Tuple
from .logger import LoggerFactory, ErrorTracker, ProgressTracker


class AsyncDownloader:
    """Asynchronous file downloader with progress tracking"""
    def __init__(self, concurrent_limit: int = 50,
                 chunk_size: int = 8192, timeout: int = 30):
        self.concurrent_limit = concurrent_limit
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(concurrent_limit)
        self.total_files = 0
        self.downloaded = 0
        self.failed_downloads: List[Tuple[str, str]] = []

        self.logger = LoggerFactory.create_logger(
            'AsyncDownloader',
            file_prefix='downloader'
        )
        self.error_tracker = ErrorTracker(self.logger)
        self.progress_tracker: ProgressTracker = None

    async def download_file(self, url: str, filepath: str, retries: int = 3) -> bool:
        """Download single file with retry logic"""
        for attempt in range(retries):
            try:
                async with self.semaphore:
                    async with aiohttp.ClientSession(
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                        ) as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                await makedirs(os.path.dirname(filepath), exist_ok=True)

                                async with aiofiles.open(filepath, 'wb') as f:
                                    async for chunk in response.content.iter_chunked(
                                              self.chunk_size
                                          ):
                                        await f.write(chunk)

                                self.downloaded += 1
                                if self.progress_tracker:
                                    self.progress_tracker.update(1, f"Downloaded {url}")
                                return True

                            self.error_tracker.log_error(
                                'http_error',
                                f"Status {response.status} for {url}",
                                {'attempt': attempt + 1}
                            )

                            if response.status == 404:
                                break

            except Exception as e:
                self.error_tracker.log_error(
                    'download_error',
                    f"Failed to download {url}: {str(e)}",
                    {'attempt': attempt + 1}
                )
                if attempt == retries - 1:
                    self.failed_downloads.append((url, filepath))
                await asyncio.sleep(1)

        return False

    async def download_batch(self, items: List[Tuple[str, str]]) -> List[bool]:
        """Download a batch of files"""
        self.total_files = len(items)
        self.progress_tracker = ProgressTracker(
            self.logger,
            self.total_files,
            update_frequency=100
        )

        tasks = []
        for url, filepath in items:
            tasks.append(self.download_file(url, filepath))

        results = await asyncio.gather(*tasks)

        if self.progress_tracker:
            self.progress_tracker.update(0, "Batch download complete")

        return results

    def save_failed_downloads(self) -> None:
        """Save failed downloads to file"""
        if self.failed_downloads:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            failed_file = f'failed_downloads_{timestamp}.txt'

            try:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    for url, filepath in self.failed_downloads:
                        f.write(f'{url}\t{filepath}\n')
                self.logger.info(f"Saved failed downloads to {failed_file}")
            except Exception as e:
                self.error_tracker.log_error(
                    'file_error',
                    f"Failed to save failed downloads: {str(e)}"
                )
