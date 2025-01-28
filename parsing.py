from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import os
from typing import Optional, List, Dict, Any, Tuple, Callable, Union
from collections import defaultdict
from aiologger import LoggerFactory, ErrorTracker


class MetadataExtractor:
    """Extract and process metadata from various sources"""
    def __init__(self, cleaners: Optional[Dict[str, Callable[[str], str]]] = None):
        self.cleaners = cleaners or {}
        self.logger = LoggerFactory.create_logger('MetadataExtractor')
        self.error_tracker = ErrorTracker(self.logger)

    def extract_from_html(
        self,
        html: Union[str, BeautifulSoup],
        selectors: Dict[str, Union[str, Tuple[str, str]]]
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
                    selector, attribute = selector_info
                    if elem := soup.select_one(selector):
                        metadata[key] = elem.get(attribute, '').strip()

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


class MetadataManager:
    """Manage metadata files and operations"""
    def __init__(self, base_dir: str = 'metadata'):
        self.base_dir = base_dir
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.index: Dict[str, List[str]] = defaultdict(list)
        self.logger = LoggerFactory.create_logger('MetadataManager')
        self.error_tracker = ErrorTracker(self.logger)

    def load_all(self, subdirs: Optional[List[str]] = None) -> None:
        """Load all metadata files from directory"""
        subdirs = subdirs or [d for d in os.listdir(self.base_dir)
                            if os.path.isdir(os.path.join(self.base_dir, d))]

        for subdir in subdirs:
            dir_path = os.path.join(self.base_dir, subdir)
            if not os.path.isdir(dir_path):
                continue

            for filename in os.listdir(dir_path):
                if filename.endswith('.json'):
                    filepath = os.path.join(dir_path, filename)
                    try:
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
        """Save metadata to file"""
        if 'id' not in data:
            self.error_tracker.log_error(
                'validation_error',
                "Metadata must contain 'id' field",
                {'data': data}
            )
            raise ValueError("Metadata must contain 'id' field")

        save_dir = os.path.join(self.base_dir, subdir) if subdir else self.base_dir
        os.makedirs(save_dir, exist_ok=True)

        filepath = os.path.join(save_dir, f"{data['id']:08d}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.cache[data['id']] = data
            self._index_metadata(data)
            self.logger.info(f"Saved metadata to {filepath}")
            return filepath
        except Exception as e:
            self.error_tracker.log_error(
                'save_error',
                f"Failed to save metadata: {str(e)}",
                {'filepath': filepath}
            )
            raise


class ContentParser:
    """Parse and extract content from HTML"""
    def __init__(self):
        self.logger = LoggerFactory.create_logger('ContentParser')
        self.error_tracker = ErrorTracker(self.logger)

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
