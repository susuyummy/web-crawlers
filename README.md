# Web Crawlers

A collection of web crawlers for various websites.

## Installation

```bash
pip install web-crawlers
```

## Usage

### PTT Gossip Crawler

```python
from web_crawlers import PTTGossipCrawler

# Create crawler instance
crawler = PTTGossipCrawler()

# Crawl articles
articles = crawler.crawl(pages=1)

# Save to Excel
crawler.save_to_excel(articles)
```

## Features

- PTT Gossip board crawler
- Save articles to SQLite database
- Export to Excel file
- Automatic content cleaning
- Rate limiting to avoid being blocked

## License

This project is licensed under the MIT License - see the LICENSE file for details. 