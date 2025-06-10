import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random
from dataclasses import dataclass
from typing import List, Optional
import sqlite3
import os

@dataclass
class Article:
    title: str
    author: str
    date: str
    url: str
    content: str

class PTTGossipCrawler:
    def __init__(self):
        self.base_url = "https://www.ptt.cc/bbs/Gossiping"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.db_path = "ptt_articles.db"
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 資料庫"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                title TEXT,
                author TEXT,
                date TEXT,
                url TEXT UNIQUE,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """獲取頁面內容"""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching page {url}: {e}")
            return None

    def _parse_article(self, article_url: str) -> Optional[Article]:
        """解析單篇文章"""
        soup = self._get_page(article_url)
        if not soup:
            return None

        try:
            main_content = soup.find('div', id='main-content')
            if not main_content:
                return None

            # 獲取標題
            title = main_content.find('span', class_='article-meta-value').text.strip()

            # 獲取作者
            author = main_content.find_all('span', class_='article-meta-value')[1].text.strip()

            # 獲取日期
            date = main_content.find_all('span', class_='article-meta-value')[3].text.strip()

            # 獲取內容
            content = main_content.text.split('--')[0].strip()

            return Article(
                title=title,
                author=author,
                date=date,
                url=article_url,
                content=content
            )
        except Exception as e:
            print(f"Error parsing article {article_url}: {e}")
            return None

    def crawl(self, pages: int = 1) -> List[Article]:
        """爬取指定頁數的文章"""
        articles = []
        current_url = f"{self.base_url}/index.html"

        for _ in range(pages):
            soup = self._get_page(current_url)
            if not soup:
                break

            # 獲取文章連結
            article_links = soup.find_all('div', class_='title')
            for link in article_links:
                a_tag = link.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    article_url = f"https://www.ptt.cc{a_tag['href']}"
                    article = self._parse_article(article_url)
                    if article:
                        articles.append(article)
                        self._save_to_db(article)
                    time.sleep(random.uniform(1, 3))  # 隨機延遲

            # 獲取上一頁的連結
            prev_link = soup.find('a', string='‹ 上頁')
            if prev_link and 'href' in prev_link.attrs:
                current_url = f"https://www.ptt.cc{prev_link['href']}"
            else:
                break

        return articles

    def _save_to_db(self, article: Article):
        """保存文章到資料庫"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT OR IGNORE INTO articles (title, author, date, url, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (article.title, article.author, article.date, article.url, article.content))
            conn.commit()
        except Exception as e:
            print(f"Error saving to database: {e}")
        finally:
            conn.close()

    def save_to_excel(self, articles: List[Article], filename: str = "ptt_articles.xlsx"):
        """將文章保存為 Excel 文件"""
        df = pd.DataFrame([{
            '標題': article.title,
            '作者': article.author,
            '日期': article.date,
            '連結': article.url,
            '內容': article.content
        } for article in articles])
        
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"已保存 {len(articles)} 篇文章到 {filename}")

    def get_all_articles_from_db(self) -> List[Article]:
        """從資料庫獲取所有文章"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT title, author, date, url, content FROM articles')
        rows = c.fetchall()
        conn.close()
        
        return [Article(title=row[0], author=row[1], date=row[2], url=row[3], content=row[4]) 
                for row in rows] 