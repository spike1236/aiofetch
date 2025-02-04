# aiofetch

A Python toolkit for asynchronous web scraping, file handling, and logging utilities.

## Features

- Asynchronous web crawling with rate limiting and retry logic
- HTML content parsing and metadata extraction
- Efficient file downloading with progress tracking
- TSV/JSON file handling utilities
- Comprehensive error tracking and logging
- Configurable batch processing

## Installation

```bash
git clone https://github.com/spike1236/aiofetch.git
pip install -r requirements.txt
```

## Key Components

- **AsyncDownloader**: Parallel file downloading with progress tracking
- **BaseCrawler**: Extensible crawler base class with domain validation
- **BatchProcessor**: Process items in configurable batches
- **RateLimiter**: Control request frequency
- **MetadataExtractor**: HTML metadata extraction with custom selectors
- **PathHandler**: Path and filename utilities
- **FileIO**: Async/sync file operations
- **TSVHandler**: TSV file reading and writing
- **LoggerFactory**: Enhanced logging with file and console outputs

## Requirements

- Python 3.9+
- aiofiles
- aiohttp
- BeautifulSoup4

## Usage Example

```python
from aiofetch import AsyncDownloader, MetadataExtractor

# Initialize downloader
downloader = AsyncDownloader(concurrent_limit=50)

# Download files in parallel
urls = [("https://example.com/file1", "file1.pdf"),
    ("https://example.com/file2", "file2.pdf")]
await downloader.download_batch(urls)

# Extract metadata
extractor = MetadataExtractor()
metadata = extractor.extract_from_html(html, {
    'title': 'h1.title',
    'date': ('meta[name="date"]', 'content')
})
```

## License

MIT License - see LICENSE file for details