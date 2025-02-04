import os
import re
import json
import aiofiles
from aiofiles.os import makedirs
from typing import AsyncGenerator, Generator, List, Optional, Union, Dict, Any
from aiologger import LoggerFactory, ErrorTracker


class PathHandler:
    """Utilities for path and filename handling"""
    def __init__(self):
        self.logger = LoggerFactory.create_logger('PathHandler')
        self.error_tracker = ErrorTracker(self.logger)

    @staticmethod
    def clean_filename(url: str, domain: str) -> str:
        """Clean and format filename from URL"""
        try:
            filename = url.split('/')[-1]
            path = url.replace(filename, '')
            path = path.replace('wp-content/', '')
            path = path.replace('https://', '').replace('http://', '')
            path = path.replace(domain, '')
            path = re.sub(r'^/+', '', path)
            path = path.replace('/', '_')
            return path + filename
        except Exception as e:
            logger = LoggerFactory.create_logger('PathHandler')
            error_tracker = ErrorTracker(logger)
            error_tracker.log_error(
                'filename_cleaning_error',
                f"Failed to clean filename: {str(e)}",
                {'url': url, 'domain': domain}
            )
            return url.split('/')[-1]  # Fallback to default filename

    @staticmethod
    def ensure_dir(path: str) -> str:
        """Ensure directory exists"""
        try:
            os.makedirs(path, exist_ok=True)
            return path
        except Exception as e:
            logger = LoggerFactory.create_logger('PathHandler')
            error_tracker = ErrorTracker(logger)
            error_tracker.log_error(
                'directory_creation_error',
                f"Failed to create directory: {str(e)}",
                {'path': path}
            )
            raise

    @staticmethod
    def join_paths(*paths: str) -> str:
        """Join path components safely"""
        return os.path.join(*[str(p).strip('/') for p in paths if p])


class FileIO:
    """Async and sync file operations"""
    def __init__(self):
        self.logger = LoggerFactory.create_logger('FileIO')
        self.error_tracker = ErrorTracker(self.logger)
        self._validate_initialization()

    def _validate_initialization(self) -> None:
        """Validate initial configuration"""
        if not os.access(os.getcwd(), os.W_OK):
            raise PermissionError("No write permission in current directory")

    async def write_chunks(
        self,
        filepath: str,
        content_iterator: AsyncGenerator[bytes, None],
        chunk_size: int = 8192
    ) -> None:
        """
        Write content in chunks asynchronously
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        try:
            await makedirs(os.path.dirname(filepath), exist_ok=True)
            async with aiofiles.open(filepath, 'wb') as f:
                async for chunk in content_iterator:
                    await f.write(chunk)
            self.logger.info(f"Successfully wrote file: {filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'file_write_error',
                f"Failed to write file: {str(e)}",
                {'filepath': filepath}
            )
            raise

    async def read_lines(
        self,
        filepath: str,
        skip_header: bool = False
    ) -> AsyncGenerator[str, None]:
        """Read lines from file asynchronously"""
        try:
            async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
                if skip_header:
                    await f.readline()
                async for line in f:
                    yield line.strip()
        except Exception as e:
            self.error_tracker.log_error(
                'file_read_error',
                f"Failed to read file: {str(e)}",
                {'filepath': filepath}
            )
            raise

    def save_json(
        self,
        data: Union[Dict[str, Any], List[Any]],
        filepath: str,
        ensure_dir: bool = True
    ) -> None:
        """Save data as JSON"""
        try:
            if ensure_dir:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Successfully saved JSON to: {filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'json_save_error',
                f"Failed to save JSON: {str(e)}",
                {'filepath': filepath}
            )
            raise


class TSVHandler:
    """TSV file handling utilities"""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.logger = LoggerFactory.create_logger('TSVHandler')
        self.error_tracker = ErrorTracker(self.logger)

    def read_rows(self, skip_header: bool = True) -> Generator[List[str], None, None]:
        """Read TSV rows as generator"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                if skip_header:
                    next(f)
                for line in f:
                    if line.strip():
                        yield line.strip().split('\t')
        except Exception as e:
            self.error_tracker.log_error(
                'tsv_read_error',
                f"Failed to read TSV file: {str(e)}",
                {'filepath': self.filepath}
            )
            raise

    def write_rows(self, rows: List[List[str]], header: Optional[List[str]] = None):
        """Write rows to TSV file"""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                if header:
                    f.write('\t'.join(header) + '\n')
                for row in rows:
                    f.write('\t'.join(map(str, row)) + '\n')
            self.logger.info(f"Successfully wrote TSV file: {self.filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'tsv_write_error',
                f"Failed to write TSV file: {str(e)}",
                {'filepath': self.filepath}
            )
            raise

    def append_row(self, row: List[str]) -> None:
        """Append single row to TSV file"""
        try:
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write('\t'.join(map(str, row)) + '\n')
            self.logger.info(f"Appended row to TSV file: {self.filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'tsv_append_error',
                f"Failed to append row to TSV file: {str(e)}",
                {'filepath': self.filepath}
            )
            raise
