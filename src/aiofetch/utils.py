import os
import re
import json
import aiofiles
from typing import Tuple, List, Dict, Any
from typing import Optional, Union, AsyncGenerator, Generator, Callable
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import defaultdict
from .logger import LoggerFactory, ErrorTracker


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
        self.path_handler = PathHandler()
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
            await aiofiles.os.makedirs(os.path.dirname(filepath), exist_ok=True)
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

    async def write(self, filepath: str, content: str, encoding: str = 'utf-8') -> None:
        """Write content to file asynchronously"""
        try:
            async def string_generator():
                yield content.encode(encoding)

            await self.write_chunks(filepath, string_generator())
            self.logger.info(f"Successfully wrote text to file: {filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'text_write_error',
                f"Failed to write text: {str(e)}",
                {'filepath': filepath}
            )
            raise

    async def append(self, filepath: str, content: str, encoding: str = 'utf-8') -> None:
        """Append content to file asynchronously"""
        try:
            await aiofiles.os.makedirs(os.path.dirname(filepath), exist_ok=True)
            async with aiofiles.open(filepath, 'a', encoding=encoding) as f:
                await f.write(content)
            self.logger.info(f"Successfully appended text to file: {filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'text_append_error',
                f"Failed to append text: {str(e)}",
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

    async def write_json(
        self,
        data: Union[Dict[str, Any], List[Any]],
        filepath: str,
        ensure_dir: bool = True
    ) -> None:
        """Write data as JSON file asynchronously"""
        try:
            if ensure_dir:
                await aiofiles.os.makedirs(os.path.dirname(filepath), exist_ok=True)

            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            await self.write(filepath, json_str)

            self.logger.info(f"Successfully wrote JSON to: {filepath}")
        except Exception as e:
            self.error_tracker.log_error(
                'json_write_error',
                f"Failed to write JSON: {str(e)}",
                {'filepath': filepath}
            )
            raise

    def ensure_path(self, filepath: str) -> str:
        """Ensure directory exists for given filepath"""
        return self.path_handler.ensure_dir(os.path.dirname(filepath))

    def join_paths(self, *paths: str) -> str:
        """Use PathHandler to join paths"""
        return self.path_handler.join_paths(*paths)


class MetadataExtractor:
    """Extract and process metadata from various sources"""
    def __init__(self, cleaners: Optional[Dict[str, Callable[[str], str]]] = None):
        self.cleaners = cleaners or {}
        self.logger = LoggerFactory.create_logger('MetadataExtractor')
        self.error_tracker = ErrorTracker(self.logger)
        self.file_io = FileIO()

    def extract_from_html(
        self,
        html: Union[str, BeautifulSoup],
        selectors: Dict[str, Union[str, Tuple]]
    ) -> Dict[str, str]:
        """Extract metadata using CSS selectors"""
        try:
            soup = BeautifulSoup(html, 'html.parser') if isinstance(html, str) else html
            metadata = {}
            for key, selector_info in selectors.items():
                if isinstance(selector_info, str):
                    if elem := soup.select_one(selector_info):
                        metadata[key] = elem.text.strip()
                elif isinstance(selector_info, tuple):
                    if len(selector_info) == 2:
                        selector, attribute = selector_info
                        if elem := soup.select_one(selector):
                            metadata[key] = elem.get(attribute, '').strip()
                    elif len(selector_info) >= 3:
                        # Supports additional parameters (e.g. index for list-type attributes)
                        selector, attribute, index = selector_info[:3]
                        if elem := soup.select_one(selector):
                            attr_value = elem.get(attribute, '')
                            if isinstance(attr_value, list) and len(attr_value) > index:
                                metadata[key] = attr_value[index]
                            elif isinstance(attr_value, str):
                                # If attribute is a string, try splitting by whitespace as a fallback
                                parts = attr_value.split()
                                metadata[key] = parts[index] if len(parts) > index else ''
                            else:
                                metadata[key] = ''
            return self._clean_metadata(metadata)
        except Exception as e:
            self.error_tracker.log_error(
                'extraction_error',
                f"Failed to extract metadata: {str(e)}",
                {'selectors': selectors}
            )
            return {}

    def _clean_metadata(self, metadata: Dict[str, str]) -> Dict[str, str]:
        """Clean extracted metadata using registered cleaners"""
        cleaned = {}
        for key, value in metadata.items():
            if key in self.cleaners:
                try:
                    cleaned[key] = self.cleaners[key](value)
                except Exception as e:
                    self.error_tracker.log_error(
                        'cleaning_error',
                        f"Failed to clean metadata for key '{key}': {str(e)}",
                        {'value': value}
                    )
                    cleaned[key] = value
            else:
                cleaned[key] = value
        return cleaned

    async def save_extracted_metadata(self, metadata: Dict[str, str], filepath: str):
        """Save extracted metadata using FileIO"""
        try:
            await self.file_io.write_json(metadata, filepath)
        except Exception as e:
            self.error_tracker.log_error(
                'save_metadata_error',
                f"Failed to save extracted metadata: {str(e)}",
                {'filepath': filepath}
            )


class MetadataManager:
    """Manage metadata files and operations"""
    def __init__(self, base_dir: str = 'metadata'):
        self.base_dir = base_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, List[str]] = defaultdict(list)
        self.logger = LoggerFactory.create_logger('MetadataManager')
        self.error_tracker = ErrorTracker(self.logger)
        self.file_io = FileIO()
        self.path_handler = PathHandler()

    def load_all(self, subdirs: Optional[List[str]] = None) -> None:
        """Load all metadata files from directory"""
        subdirs = subdirs or [d for d in os.listdir(self.base_dir)
                            if os.path.isdir(self.path_handler.join_paths(self.base_dir,
                                                                          d))]

        for subdir in subdirs:
            dir_path = self.path_handler.join_paths(self.base_dir, subdir)
            if not os.path.isdir(dir_path):
                continue

            for filename in os.listdir(dir_path):
                if filename.endswith('.json'):
                    try:
                        filepath = self.path_handler.join_paths(dir_path, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if 'id' in data:
                                self.cache[data['id']] = data
                                self._index_metadata(data)
                    except Exception as e:
                        self.error_tracker.log_error(
                            'load_error',
                            f"Error loading {filepath}: {str(e)}"
                        )

    def _index_metadata(self, data: Dict[str, Any]) -> None:
        """Index metadata for quick lookups"""
        for key, value in data.items():
            if isinstance(value, (str, int)):
                self.index[key].append(data['id'])

    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Find metadata by ID"""
        return self.cache.get(id)

    def find_by_field(self, field: str, value: Union[str, int]) -> List[Dict[str, Any]]:
        """Find metadata entries by field value"""
        ids = self.index.get(field, [])
        return [self.cache[id] for id in ids
                if self.cache[id].get(field) == value]

    def save_metadata(self, data: Dict[str, Any], subdir: Optional[str] = None) -> str:
        """Save metadata using FileIO"""
        if 'id' not in data:
            raise ValueError("Metadata must contain 'id' field")

        save_dir = self.path_handler.join_paths(self.base_dir, subdir or '')
        self.path_handler.ensure_dir(save_dir)

        filepath = self.path_handler.join_paths(save_dir, f"{data['id']:08d}.json")
        self.file_io.save_json(data, filepath, ensure_dir=False)  # Already ensured

        self.cache[data['id']] = data
        self._index_metadata(data)
        return filepath


class ContentParser:
    """Parse and extract content from HTML"""
    def __init__(self):
        self.logger = LoggerFactory.create_logger('ContentParser')
        self.error_tracker = ErrorTracker(self.logger)
        self.metadata_extractor = MetadataExtractor()
        self.file_io = FileIO()

    @staticmethod
    def extract_links(
        html: Union[str, BeautifulSoup],
        base_url: Optional[str] = None,
        selector: str = 'a[href]'
    ) -> List[Dict[str, str]]:
        """Extract links from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser') if isinstance(html, str) else html
            links = []

            for link in soup.select(selector):
                href = link.get('href', '').strip()
                if href and not href.startswith(('#', 'javascript:')):
                    if base_url:
                        href = urljoin(base_url, href)
                    links.append({
                        'url': href,
                        'text': link.text.strip(),
                        'title': link.get('title', '').strip()
                    })

            return links
        except Exception as e:
            logger = LoggerFactory.create_logger('ContentParser')
            error_tracker = ErrorTracker(logger)
            error_tracker.log_error(
                'link_extraction_error',
                f"Failed to extract links: {str(e)}",
                {'selector': selector}
            )
            return []

    @staticmethod
    def extract_images(
        html: Union[str, BeautifulSoup],
        base_url: Optional[str] = None,
        selector: str = 'img[src]'
    ) -> List[Dict[str, str]]:
        """Extract images from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser') if isinstance(html, str) else html
            images = []

            for img in soup.select(selector):
                src = img.get('src', '').strip()
                if src:
                    if base_url:
                        src = urljoin(base_url, src)
                    images.append({
                        'url': src,
                        'alt': img.get('alt', '').strip(),
                        'title': img.get('title', '').strip()
                    })

            return images
        except Exception as e:
            logger = LoggerFactory.create_logger('ContentParser')
            error_tracker = ErrorTracker(logger)
            error_tracker.log_error(
                'image_extraction_error',
                f"Failed to extract images: {str(e)}",
                {'selector': selector}
            )
            return []

    async def save_extracted_content(self, content: Dict[str, Any], filepath: str):
        """Save extracted content using FileIO"""
        try:
            await self.file_io.write_json(content, filepath)
        except Exception as e:
            self.error_tracker.log_error(
                'content_save_error',
                f"Failed to save extracted content: {str(e)}",
                {'filepath': filepath}
            )
