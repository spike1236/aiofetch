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

- We are going to scrape images and books data from the example website - books.toscrape.com.

```python3
import os
import asyncio
from urllib.parse import urljoin
from aiofetch.crawler import BaseCrawler, RateLimiter
from aiofetch.utils import MetadataExtractor, FileIO
from aiofetch.downloader import AsyncDownloader


class BookScraper(BaseCrawler):
    def __init__(self, base_url: str):
        super().__init__(base_url)
        self.extractor = MetadataExtractor()
        self.rate_limiter = RateLimiter()

    async def scrape_page(self, url: str) -> list:
        async with self.rate_limiter:
            content = await self.fetch_page(url)
            if not content:
                return []
            self.logger.debug(f"Parsing HTML content from {url}")
            soup = await self.parse_html(content)
            books = []
            selectors = {
                'title': ('h3 a', 'title'),
                'relative_link': ('h3 a', 'href'),
                'price': 'p.price_color',
                'availability': 'p.instock.availability',
                'rating': ('p.star-rating', 'class', 1),
                'image': ('div.image_container img', 'src')
            }
            for article in soup.select('article.product_pod'):
                data = self.extractor.extract_from_html(article, selectors)
                if rel := data.pop('relative_link', None):
                    data['url'] = urljoin(url, rel)
                else:
                    data['url'] = url
                if img := data.get('image'):
                    data['image'] = urljoin(url, img)
                books.append(data)
        return books

    async def scrape(self, start_url: str) -> list:
        return await self.scrape_page(start_url)


async def main():
    # Scrape book data
    async with BookScraper("http://books.toscrape.com") as scraper:
        books = await scraper.scrape("http://books.toscrape.com/catalogue/page-1.html")
    
    # Save scraped data as JSON
    file_io = FileIO()
    json_path = "data/books.json"
    await file_io.write_json(books, json_path)
    print(f"Saved {len(books)} books to {json_path}")
    
    # Prepare and download images
    download_tasks = []
    for book in books:
        if image_url := book.get('image'):
            filename = os.path.basename(image_url)
            local_path = os.path.join("images", filename)
            download_tasks.append((image_url, local_path))
    
    if download_tasks:
        downloader = AsyncDownloader(concurrent_limit=10)
        results = await downloader.download_batch(download_tasks)
        print(f"Downloaded {sum(results)} images out of {len(download_tasks)}")
        downloader.save_failed_downloads()


if __name__ == "__main__":
    asyncio.run(main())
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request or Issue.

## Author

Akram Rakhmetulla ([akram042006@gmail.com](mailto:akram042006@gmail.com))