# aiofetch

A Python toolkit for asynchronous web scraping with built-in error tracking and metadata management.

## Features

### Web Processing
- Asynchronous file downloading with progress tracking
- Rate limiting with configurable delays
- Smart retry logic with timeout handling
- Domain-aware crawling with URL validation

### Content Processing
- Flexible HTML content parsing
- Custom selector-based metadata extraction
- Automated link and image extraction
- URL normalization and path handling

### File & Data Management
- Asynchronous file operations
- Concurrent chunk-based downloads
- Smart path handling and file naming
- JSON data management with validation

### Error Handling & Progress Tracking
- Comprehensive error tracking and reporting
- Progress monitoring for long operations
- Detailed logging with configurable outputs
- Operation statistics and summaries

### Metadata Management
- Efficient in-memory caching
- Field-based search functionality
- Automatic metadata indexing
- Structured data validation

## Installation

```bash
pip install aiofetch
```

## Key Components

- **AsyncDownloader**: Parallel file downloading with progress tracking
- **BatchProcessor**: Process items in configurable batches
- **RateLimiter**: Control request frequency
- **MetadataExtractor**: HTML metadata extraction with custom selectors
- **PathHandler**: Path and filename utilities
- **FileIO**: Async/sync file operations
- **BaseCrawler**: Extensible crawler base class with domain validation
- **LoggerFactory**: Enhanced logging with file and console outputs

## Requirements

- Python 3.9+
- aiofiles
- aiohttp
- BeautifulSoup4

## Quick start
```python3
import asyncio
from aiofetch import (
    AsyncDownloader,
    MetadataExtractor,
    ContentParser,
    FileIO
)

async def main():
    # Initialize components
    downloader = AsyncDownloader(concurrent_limit=20)
    parser = ContentParser()
    file_io = FileIO()
    
    # Download files
    urls = [
        ("https://example.com/file1.pdf", "downloads/file1.pdf"),
        ("https://example.com/file2.pdf", "downloads/file2.pdf")
    ]
    await downloader.download_batch(urls)
    
    # Parse HTML content
    html = """<html><body>
        <h1>Title</h1>
        <img src="image.jpg" alt="Test">
    </body></html>"""
    
    # Extract metadata
    extractor = MetadataExtractor()
    metadata = extractor.extract_from_html(html, {
        'title': 'h1',
        'images': ('img', 'src')
    })
    
    # Save results
    await file_io.save_json(metadata, 'output/metadata.json')

if __name__ == "__main__":
    asyncio.run(main())
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or Issue.

## Author

Akram Rakhmetulla ([akram042006@gmail.com](mailto:akram042006@gmail.com))