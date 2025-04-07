# yinyu_Spider.py
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.BaseSpider import BaseSpider
from utils.TqdmLogHandler import logger
from utils.WebUtils import WebUtils
from utils.dealer_en import dealer_en


class yinyuSpider(BaseSpider):
    """英语小说章节爬虫"""

    def __init__(self, config=None):
        self.base_dir = "yinyu"
        super().__init__(f"{self.base_dir}", config or {})
        # self.processed_urls = None
        self.base_url = "https://www.yingyuxiaoshuo.com/"
        self.visited_urls = set()
        self.timeout = self.config.get("timeout", 10)
        self.current_url = self.base_url

        # 断点续传
        self.csv_file = Path(f"parsed/yingyu_crawl_records.csv")
        self._init_csv()
        self.load_processed_urls()
        self.sourcefile = None

    def _init_csv(self):
        """初始化CSV文件并写入表头"""
        # 创建父目录（自动递归创建）
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'timestamp',
                    'url',
                    'source_file',
                    'parsed_file',
                    'book_name',
                    'chapter_name',
                    'status'
                ])
                writer.writeheader()

    def load_processed_urls(self):
        """加载已处理的URL"""
        # self.processed_urls = set()
        self.visited_urls = set()
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['url'] and row['status'] == 'success':
                        # self.processed_urls.add(row['url'])
                        self.visited_urls.add(row['url'])
        except FileNotFoundError:
            pass

    def _update_csv(self, record: dict):
        """更新CSV记录"""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=record.keys())
                writer.writerow(record)
        except Exception as e:
            logger.error(f"CSV记录更新失败: {str(e)}")

    def _get_source_file(self, url: str, direction: str, file_name=None):
        """记录原始文件信息"""
        if not file_name:
            file_name = WebUtils.generate_filename(url)
            file_name = self.sanitize_filename(file_name)
        self.sourcefile = Path("origin") / direction / file_name

    def sanitize_filename(self, name: str) -> str:
        """替换非法字符为下划线"""
        return re.sub(r'[\\/*?:"<>|]', '_', name).strip()

    def fetch_content(self, url: str, direction: str, file_name: str = None) -> Optional[str]:
        """统一封装的内容获取方法"""
        if url in self.visited_urls:
            logger.warning(f"⏩ 跳过已保存URL: {url}")
            return None

        self.visited_urls.add(url)
        self.random_delay()
        logger.info(f"📖 访问URL: {url}")
        content = self.fetcher.fetch_and_save(
            url=url,
            direction=direction,
            file_name=file_name,
            save_origin=True
        )
        if content:
            self._get_source_file(url, direction, file_name)
        if not content:
            logger.error(f"🛑 获取内容失败: {url}")
        return content

    def _extract_books(self, content: str) -> Optional[Dict]:
        """书籍列表解析"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            title = soup.find('title').get_text(strip=True) if soup.title else "No Title"

            # 使用精确的CSS选择器
            book_links = soup.select(
                'h2.inline.italic.text-xs.text-gray1.hover\\:text-hover1.max-sm\\:hidden.ml-2 a'
            )

            books = []
            for link in book_links:
                if not (name := link.get_text(strip=True)):
                    continue
                if not (url := urljoin(self.base_url, link.get('href'))):
                    continue
                books.append({"name": name, "url": url})

            return {"title": title, "books": books, "source_url": self.current_url}
        except Exception as e:
            logger.error(f"书籍列表解析失败: {str(e)}", exc_info=True)
            return None

    def _extract_chapters(self, content: str) -> Optional[Dict]:
        """章节列表解析"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            book_name_elem = soup.select_one('h2.text-sm.inline.ml-2.max-sm\\:hidden')
            book_name = book_name_elem.get_text(strip=True) if book_name_elem else "Unknown Book"

            chapter_links = soup.select('a.text-danger.hover\\:text-hover1[href]')

            chapters = []
            for link in chapter_links:
                if not (name := link.get_text(strip=True)):
                    continue
                if not (url := urljoin(self.base_url, link.get('href'))):
                    continue
                chapters.append({"chapter_name": name, "url": url})

            return {"book_name": book_name, "chapters": chapters}
        except Exception as e:
            logger.error(f"章节列表解析失败: {str(e)}", exc_info=True)
            return None

    def _extract_chapter_content(self, content: str) -> Optional[Dict]:
        """章节内容解析"""
        try:
            soup = BeautifulSoup(content, 'lxml')
            title_elem = soup.select_one('h2.text-danger.text-center.text-lg.font-bold.mt-2')
            chapter_name = title_elem.get_text(strip=True) if title_elem else "Unknown Chapter"

            content_elems = soup.select('div.c-en')
            content_text = "\n".join([elem.get_text(strip=True) for elem in content_elems])

            return {"chapter_name": chapter_name, "content": content_text}
        except Exception as e:
            logger.error(f"章节内容解析失败: {str(e)}", exc_info=True)
            return None

    def process_book(self, book_url: str, book_name: str) -> None:
        """处理单个书籍的完整流程"""
        content = self.fetch_content(book_url, f"{self.base_dir}/{book_name}")
        if not content:
            return

        chapters_data = self._extract_chapters(content)
        if not chapters_data:
            logger.error(f"书籍章节解析失败: {book_name}")
            return

        for chapter in chapters_data.get("chapters", []):
            self.process_chapter(chapter, book_name)

    def process_chapter(self, chapter: Dict, book_name: str) -> None:
        """处理单个章节的完整流程"""
        chapter_url = chapter["url"]
        # 规范书名与章节名
        sanitized_book_name = self.sanitize_filename(book_name)
        sanitized_chapter_name = self.sanitize_filename(chapter['chapter_name'])
        file_name = f"{sanitized_book_name}-{sanitized_chapter_name}.html"

        content = self.fetch_content(
            chapter_url,
            f"{self.base_dir}/{sanitized_book_name}",
            file_name=file_name
        )
        if not content:
            return

        chapter_data = self._extract_chapter_content(content)
        if not chapter_data:
            logger.error(f"章节内容解析失败: {chapter_url}")
            return

        self._save_chapter_data(
            book_name=book_name,
            chapter_name=chapter_data["chapter_name"],
            chapter_url=chapter_url,
            content=chapter_data["content"]
        )

        # 处理章节内容
        text = self.dealer.clean_text(chapter_data["content"], uppercase=False)
        self.dealer._save_chapter_data(
            book_name=book_name,
            chapter_name=chapter_data["chapter_name"],
            text=text)

    def _save_chapter_data(self, book_name: str, chapter_name: str,
                           chapter_url: str, content: str) -> None:
        """统一的章节保存方法"""
        try:
            # 生成安全文件名
            safe_book_name = self.sanitize_filename(book_name)[:50]
            safe_chapter_name = self.sanitize_filename(chapter_name)[:50]

            # 创建存储路径
            save_dir = Path("parsed") / safe_book_name
            save_dir.mkdir(parents=True, exist_ok=True)

            # 预处理后的章节目录
            dealer_dir = save_dir / chapter_name
            dealer_dir.mkdir(parents=True, exist_ok=True)
            dealer_path = dealer_dir / f"{safe_book_name}-{safe_chapter_name}.txt"

            # 写入文件内容
            file_path = save_dir / f"{safe_chapter_name}.txt"
            with file_path.open("w", encoding="utf-8-sig") as f:
                f.write(f"Book: {book_name}\n")
                f.write(f"Chapter: {chapter_name}\n")
                f.write(f"URL: {chapter_url}\n\n")
                f.write(content)

            # 记录解析文件信息
            self._update_csv({
                'timestamp': datetime.now().isoformat(),
                'url': chapter_url,
                'source_file': str(self.sourcefile),
                'parsed_file': str(file_path),
                'book_name': book_name,
                'chapter_name': chapter_name,
                'status': "success"
            })

            logger.info(f"✅ 成功保存章节: {file_path}")
        except Exception as e:
            logger.error(f"🛑 文件保存失败: {str(e)}", exc_info=True)

    def crawl(self, max_books: int = 3) -> None:
        """优化的爬取主流程"""
        processed_count = 0
        try:
            # 处理初始页面
            if not (index_content := self.fetch_content(self.base_url, f"{self.base_dir}")):
                return

            if not (books_data := self._extract_books(index_content)):
                return

            for book in books_data.get("books", []):
                if processed_count >= max_books:
                    break

                logger.info(f"📖 开始处理书籍: {book['name']}")
                self.process_book(book["url"], book["name"])
                processed_count += 1

        except KeyboardInterrupt:
            logger.warning("⽤户中断操作")
        except Exception as e:
            logger.error(f"爬取流程异常: {str(e)}", exc_info=True)
        finally:
            logger.info(f"🎉 完成处理 {processed_count}/{max_books} 本书籍")
