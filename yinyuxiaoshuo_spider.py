# yinyu_Spider.py
import re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
from pandas.core.generic import bool_t
from utils.BaseSpider import BaseSpider
from utils.Saver import Saver
from utils.TqdmLogHandler import logger

class yinyuSpider(BaseSpider):
    """英语小说章节爬虫"""

    def __init__(self, config=None):
        super().__init__("yinyu", config or {})
        self.base_url = "https://www.yingyuxiaoshuo.com/"
        self.visited_urls = set()
        self.timeout = self.config.get("timeout", 10)
        self.current_url = self.base_url  # 跟踪当前爬取URL

    def _extract_books(self, content: str) -> Optional[Dict]:
        """解析书籍列表的强化版本"""
        try:
            html = BeautifulSoup(content, 'lxml')
            available_books = []

            # 使用更稳健的选择器
            title = html.find('title').get_text(strip=True) if html.title else "No Title"

            # 使用CSS选择器提高准确性
            # book_items = html.select('h2.inline.text-danger.hover\\:text-hover1.font-semibold a')
            # 筛选英文名
            book_items = html.select('h2.inline.italic.text-xs.text-gray1.hover\\:text-hover1.max-sm\\:hidden.ml-2 a')

            for book_link in book_items:
                if not (name := book_link.get_text(strip=True)):
                    continue

                if not (href := book_link.get('href')):
                    continue

                available_books.append({
                    "name": name,
                    "url": urljoin(self.base_url, href)
                })

            return {
                "title": title,
                "books": available_books,
                "source_url": self.current_url
            }
        except Exception as e:
            logger.error(f"解析失败: {str(e)}", exc_info=True)
            return None

    def _extract_book(self, content: str):
        """解析书籍列表的强化版本"""
        try:
            html = BeautifulSoup(content, 'lxml')
            available_chapters = []

            # 使用更稳健的选择器
            # title = html.find('title').get_text(strip=True) if html.title else "No Title"
            book_name = html.select('h2.text-sm.inline.ml-2.max-sm\\:hidden')
            # 使用CSS选择器提高准确性
            chapter_items = html.select('a.text-danger.hover\\:text-hover1[href]')

            # 获取章节名和对应的url
            for chapter_link in chapter_items:
                if not (chapter_name := chapter_link.get_text(strip=True)):
                    continue

                if not (href := chapter_link.get('href')):
                    continue
                available_chapters.append({
                    "chapter_name": chapter_name,
                    "url": urljoin(self.base_url, href)
                })

            return {
                "book_name": book_name,
                "chapters": available_chapters,
                "source_url": self.current_url
            }
        except Exception as e:
            logger.error(f"解析失败: {str(e)}", exc_info=True)
            return None

    # 解析单个章节标题及内容
    def _extract_chapter(self, content: str) -> Optional[Dict]:
        try:
            html = BeautifulSoup(content, 'lxml')
            # 使用 select_one 获取单个元素
            chapter_title = html.select_one('h2.text-danger.text-center.text-lg.font-bold.mt-2')
            chapter_name = chapter_title.get_text(strip=True) if chapter_title else None
            # 获取所有 c-en 元素并拼接内容
            content_elements = html.select('div.c-en')
            chapter_content = "\n".join([
                elem.get_text(strip=True)
                for elem in content_elements
            ])
            return {
                "chapter_name": chapter_name,
                "content": chapter_content,
            }
        except Exception as e:
            logger.error(f"解析失败: {str(e)}", exc_info=True)
            return None

    def crawl(self, max_articles: int = 3) -> None:
        """执行爬取流程（强化错误处理版本）"""
        try:
            while max_articles > 0 and self.current_url:
                # 去重检查
                if self.current_url in self.visited_urls:
                    logger.warning(f"⏩ 跳过重复URL: {self.current_url}")
                    break

                # 获取页面内容
                self.random_delay()
                content = self.fetcher.fetch_and_save(
                    url=self.current_url,
                    direction="yinyu",
                    save_origin=True
                )

                # 内容有效性验证
                if not content:
                    logger.error(f"🛑 获取内容失败: {self.current_url}")
                    break

                # 解析书籍列表
                if not (booklists := self._extract_books(content)):
                    logger.error("🛑 解析书籍列表失败")
                    break

                # 轮询书籍列表
                for book in booklists.get("books", [])[:max_articles]:
                    logger.info(f"📚 正在处理: {book['name']}")
                    book_url = book["url"]
                    book_name = book["name"]
                    if book_url:
                        # 获取页面内容
                        self.random_delay()
                        content = self.fetcher.fetch_and_save(
                            url=book_url,
                            direction="yinyu/{}".format(book_name),
                            save_origin=True
                        )
                        logger.info(book_url)
                        # 轮询每本书章节列表
                        if chapter_lists := self._extract_book(content):
                            for chapter in chapter_lists.get("chapters", []):
                                chapter_url = chapter["url"]
                                logger.info(chapter_url)
                                # 获取页面内容
                                self.random_delay()
                                content = self.fetcher.fetch_and_save(
                                    url=chapter_url,
                                    file_name="{}-{}.html".format(book_name, chapter["chapter_name"]),
                                    direction="yinyu/{}".format(book_name),
                                    save_origin=True
                                )
                                # 保存章节内容
                                if chapter_data := self._extract_chapter(content):
                                    # 组合元数据
                                    save_data = {
                                        "book_name": book_name,
                                        "chapter_name": chapter_data["chapter_name"],
                                        "chapter_url": chapter_url,
                                        "content": chapter_data["content"]
                                    }
                                    self._txt_saver([save_data])  # 包裹成列表保持接口统一

                        else: logger.info("🛑 解析章节列表失败")
                    max_articles -= 1
                    if max_articles <= 0:
                        break

        except KeyboardInterrupt:
            logger.warning("用户中断操作")
        except Exception as e:
            logger.error(f"爬取流程异常: {str(e)}", exc_info=True)
        finally:
            logger.info(f"🏁 剩余待爬数量: {max_articles}")
            logger.info("🎉 任务完成")

    def _txt_saver(self, data, base_dir="parsed"):
        """保存器：parsed/{book_name}/{chapter_name}.txt"""
        for item in data:
            if not all(key in item for key in ["book_name", "chapter_name", "content"]):
                logger.warning("⚠️ 数据字段缺失，跳过保存")
                continue
            try:
                # 准备路径组件
                book_name = item["book_name"]
                raw_chapter_name = item["chapter_name"]

                # 创建安全文件名
                clean_chapter_name = re.sub(r'[\\/*?:"<>|]', '', raw_chapter_name)
                clean_chapter_name = clean_chapter_name.replace(' ', '_')[:50]  # 限制长度
                filename = f"{clean_chapter_name}.txt"

                # 创建目录结构
                save_path = Path(base_dir) / book_name
                save_path.mkdir(parents=True, exist_ok=True)

                # 写入文件内容
                with (save_path / filename).open('w', encoding='utf-8') as f:
                    f.write(f"Book: {book_name}\n")
                    f.write(f"Chapter: {raw_chapter_name}\n")
                    f.write(f"URL: {item.get('chapter_url', '')}\n\n")
                    f.write(item["content"])

                logger.info(f"✅ 成功保存：{save_path / filename}")

            except Exception as e:
                logger.error(f"🛑 保存失败: {str(e)}", exc_info=True)