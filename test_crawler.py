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


