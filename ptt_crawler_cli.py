import argparse
from web_crawlers import PTTGossipCrawler

def main():
    parser = argparse.ArgumentParser(description='PTT 八卦版爬蟲')
    parser.add_argument('--pages', type=int, default=1, help='要爬取的頁數（預設：1）')
    parser.add_argument('--output', type=str, default='ptt_articles.xlsx', help='輸出檔案名稱（預設：ptt_articles.xlsx）')
    
    args = parser.parse_args()
    
    print("開始爬取 PTT 八卦版文章...")
    crawler = PTTGossipCrawler()
    
    try:
        articles = crawler.crawl(pages=args.pages)
        crawler.save_to_excel(articles, filename=args.output)
        
        print(f"\n已保存 {len(articles)} 篇文章到 {args.output}")
        print("\n爬取結果預覽：")
        for article in articles:
            print("\n" + "="*50)
            print("標題:", article.title)
            print("作者:", article.author)
            print("日期:", article.date)
            print("連結:", article.url)
            print("內容預覽:", article.content[:100], "...")
            
    except Exception as e:
        print(f"發生錯誤：{str(e)}")

if __name__ == '__main__':
    main() 