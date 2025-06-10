# PTT Crawler

一個簡單的 PTT 八卦版爬蟲套件。

## 安裝

```bash
pip install git+https://github.com/susuyummy/web-crawlers.git
```

## 使用方法

```python
from web_crawlers import PTTGossipCrawler

# 創建爬蟲實例
crawler = PTTGossipCrawler()

# 爬取 1 頁文章
articles = crawler.crawl(pages=1)

# 保存到 Excel
crawler.save_to_excel(articles)

# 印出結果
print("總共爬取到", len(articles), "篇文章")
for article in articles:
    print("\n" + "="*50)
    print("標題:", article.title)
    print("作者:", article.author)
    print("日期:", article.date)
    print("連結:", article.url)
    print("內容預覽:", article.content[:100], "...")
```

## 功能特點

- 自動爬取 PTT 八卦版文章
- 支援分頁爬取
- 自動保存到 SQLite 資料庫
- 導出到 Excel 文件
- 自動內容清理
- 速率限制避免被封鎖

## 依賴套件

- requests>=2.31.0
- beautifulsoup4>=4.12.0
- pandas>=2.1.0
- openpyxl>=3.1.0

## 授權

MIT License 