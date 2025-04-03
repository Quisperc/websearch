# biqu_Spider.py
import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.BaseSpider import BaseSpider
from utils.TqdmLogHandler import logger
from utils.WebUtils import WebUtils


class biquSpider(BaseSpider):
    """22笔趣小说章节爬虫

    核心功能：
    - 自动翻页式章节抓取
    - 小说正文内容解析
    - 相对路径转绝对URL
    - 章节数量控制

    网站特性适配：
    - 移动端页面适配（m.22biqu.com）
    - 下一页按钮特殊定位（id="pt_next"）
    - 章节内容容器定位（id="chaptercontent"）

    典型数据流：
    起始URL -> 解析内容 -> 获取下一页 -> 循环直至完结
    """

    def __init__(self, config=None):
        """初始化爬虫实例

        Args:
            config (dict, optional): 爬虫配置参数，可覆盖默认设置
        """
        self.base_dir = "22biqu"
        super().__init__(f"{self.base_dir}", config)  # 继承基类配置
        self.base_url = "https://m.22biqu.com/biqu5403/5419628.html"  # 初始章节URL
        # self.visited_urls = set()  # 已访问URL集合
        self.visited_urls = []  # 改用列表

        self.timeout = self.config.get("timeout", 10)
        self.current_url = self.base_url

        # 章节名
        self.chapter_name = None

        # 断点续传
        self.csv_file = Path(f"parsed/{self.base_dir}/crawl_records.csv")
        self._init_csv()
        self.load_processed_urls()
        self.sourcefile = None

    def _extract_links(self, content, current_url):
        """解析下一页链接

        定位策略：
        - 通过特定按钮定位（包含id和class复合特征）
        - 使用urljoin处理相对路径

        Args:
            content (str): 当前页面HTML内容
            current_url (str): 当前页面完整URL

        Returns:
            list: 标准化后的下一页URL列表（通常包含0-1个元素）

        Raises:
            Exception: 解析异常时记录错误日志
        """
        try:
            soup = BeautifulSoup(content, 'lxml')
            # 精准定位下一页按钮（复合选择器
            raw_links = soup.select_one('a#pt_next.Readpage_up')['href']
            # 生成绝对URL（处理分页参数）
            # return [urljoin(current_url, link) for link in raw_links]
            return [urljoin(current_url, raw_links)]
        except Exception as e:
            logger.error(f"解析链接失败: {str(e)}")
            return None

    def _extract_article(self, content, page = 0, chapter_n = None):
        """解析单章小说内容

        提取规则：
        - 正文内容合并所有文本节点
        - 保留当前URL作为数据溯源

        Args:
            content (str): 章节页面HTML内容

        Returns:
            dict/None: 包含标题、内容等字段的字典，解析失败返回None
        """
        try:
            soup = BeautifulSoup(content, 'lxml')
            # <div id="chaptercontent" class="Readarea ReadAjax_content">
            #                 <p> 第225章 玄学型侦探</p>
            # 第一个P标签内的作为chapter_name
            chapter_name = chapter_n
            if chapter_n is None:
                title_elem = soup.select_one('div#chaptercontent p:first-child')
                chapter_name = title_elem.get_text(strip=True) if title_elem else "Unknown Chapter"

                # <div id="chaptercontent" class="Readarea ReadAjax_content">
                #                 <p> 第225章 玄学型侦探
                # </p><p> 昏暗的房间内铺着一层薄薄的淡红月纱，所有的事物都影影绰绰，不够分明。
                # </p><p> 三位穿黑外套的男子分别熟睡于不同的地方，而那组小沙发上，克莱恩半融于黑夜般闭着眼睛，似乎也进入了沉眠。
                # 其余P标签作为context
                content_elems = soup.select('#chaptercontent p:not(:first-child)')
                content_text = "\n".join([elem.get_text(strip=True) for elem in content_elems])
                chapter_name = chapter_name + f"第{page + 1}页"
            if chapter_n:
                chapter_name = chapter_n
                # 其余P标签作为context
                content_elems = soup.select('#chaptercontent p')
                content_text = "\n".join([elem.get_text(strip=True) for elem in content_elems])
                chapter_name = re.sub(r'第\d+页$', '', chapter_name)
                chapter_name = chapter_name + f"第{page + 1}页"

            self._save_chapter_data(
                book_name="《诡秘之主》",
                chapter_name=chapter_name,
                chapter_url=self.current_url,
                content=content_text
            )
            return {
                "chapter_name":chapter_name,
                "chapter_url":self.current_url,
                "content":content_text
            }
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            return None

    def crawl(self, max_articles=50):
        """链式章节抓取主流程

        执行逻辑：
        1. 从初始URL开始循环
        2. 获取并解析当前章节
        3. 定位下一页链接
        4. 满足终止条件时退出（达到最大数量或无后续章节）

        Args:
            max_articles (int): 最大抓取章节数，默认50章
        """
        current_num = 0
        try:
            self.current_url = self.base_url
            while max_articles > current_num and self.current_url:
                # 获取并缓存原始页面
                page2 = current_num % 2
                page1 = int(current_num / 2)
                content = self.fetch_content(
                    self.current_url,
                    direction=f"{self.base_dir}",
                    file_name=f"《诡秘之主》-第{page1 + 1}章第{page2 + 1}页.html"
                )
                if content is None:
                    # 获取下一个链接
                    # self.current_url = self.visited_urls[current_num]
                    current_num += 1
                    continue
                # 解析正文
                if not page2:
                    self.chapter_name = self._extract_article(content,page= page2).get("chapter_name")
                else:
                    self._extract_article(content,page= page2, chapter_n=self.chapter_name)
                current_num += 1
                # 获取下一页链接（通常包含0-1个元素）
                next_links = self._extract_links(content, self.current_url)
                if not next_links:
                    logger.info("🛑 已到达最终章节")
                    break

                # 更新当前URL（实现链式跳转）
                self.current_url = next_links[0]
        except KeyboardInterrupt:
            logger.warning("⽤户中断操作")
        except Exception as e:
            logger.error(f"爬取流程异常: {str(e)}", exc_info=True)
        finally:
            logger.info(f"🎉 完成处理 {current_num}/{max_articles} 章")

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
        self.processed_urls = set()
        try:
            with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['url'] and row['status'] == 'success':
                        # self.processed_urls.add(row['url'])
                        self.visited_urls.append(row['url'])
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

    def _get_source_file(self, url: str, direction: str, file_name = None):
        """记录原始文件信息"""
        if not file_name:
            file_name = WebUtils.generate_filename(url)
        self.sourcefile = Path("origin") / direction / file_name

    def fetch_content(self, url: str, direction: str, file_name: str = None) -> Optional[str]:
        """统一封装的内容获取方法"""
        if url in self.visited_urls:
            logger.warning(f"⏩ 跳过已保存URL: {url}")
            return None

        # self.visited_urls.add(url)
        self.visited_urls.append(url)  # 按顺序记录
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

    def _save_chapter_data(self, book_name: str, chapter_name: str,
                           chapter_url: str, content: str) -> None:
        """统一的章节保存方法"""
        try:
            # 生成安全文件名
            safe_book_name = re.sub(r'[\\/*?:"<>|]', '', book_name)[:50]
            safe_chapter_name = re.sub(r'[\\/*?:"<>|]', '', chapter_name)[:50]

            # 创建存储路径
            save_dir = Path("parsed") / safe_book_name
            save_dir.mkdir(parents=True, exist_ok=True)

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