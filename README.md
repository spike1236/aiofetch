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
    BaseCrawler,
    ContentParser,  
    MetadataExtractor,
    FileIO,
    RateLimiter
)


async def main():
    # Initialize components
    crawler = BaseCrawler("https://example.com", concurrent_limit=5)
    downloader = AsyncDownloader(concurrent_limit=10)
    parser = ContentParser()
    extractor = MetadataExtractor()
    file_io = FileIO()
    rate_limiter = RateLimiter(requests_per_second=2)

    async with crawler:
        # Fetch and parse page
        html = await crawler.fetch_page("https://example.com/products")
        
        if html:
            # Extract links and metadata
            links = parser.extract_links(html, base_url=crawler.base_url)
            metadata = extractor.extract_from_html(html, {
                'title': 'h1.product-title',
                'price': ('.price', 'data-amount'),
                'description': 'meta[name="description"]',
                'images': ('img.product-image', 'src')
            })

            # Download images with rate limiting
            image_urls = [(img['url'], f"images/{i}.jpg") 
                         for i, img in enumerate(metadata.get('images', []))]
            
            async with rate_limiter:
                await downloader.download_batch(image_urls)

            # Save extracted data
            await file_io.write_json(metadata, 'data/product_metadata.json')
            
            # Results:
            print(f"Processed {len(links)} links")
            print(f"Downloaded {downloader.downloaded} images")
            print(f"Saved metadata to data/product_metadata.json")


if __name__ == "__main__":
    asyncio.run(main())
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or Issue.

## Author

Akram Rakhmetulla ([akram042006@gmail.com](mailto:akram042006@gmail.com))