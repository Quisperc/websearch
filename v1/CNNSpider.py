# CNNSpider.py
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from lxml import etree

from utils import Fetcher, Saver
import time
import random

class CNNSpider:
    def __init__(self):
        # CNN文章URL示例：https://edition.cnn.com/2023/08/15/tech/ai-robot-hand-write/index.html
        self.base_urls = [
            "https://edition.cnn.com/world",
            "https://edition.cnn.com/politics",
            "https://edition.cnn.com/business",
            "https://edition.cnn.com/tech"
        ]
        self.fetcher = Fetcher()
        self.delay_range = (1, 3)  # 随机延迟范围
        self.thread_workers = 5  # 新增可配置参数
        self.request_timeout = 10  # 新增超时控制

    def get_article_links(self, content):
        """从列表页获取文章链接"""
        html = etree.HTML(content)
        return html.xpath('//a[contains(@href, "/202")]/@href')  # 特征链接

    def crawl_section(self, section_url):
        """爬取单个板块"""
        print(f"⏳ 开始爬取板块: {section_url}")
        content = self.fetcher.fetch_and_save(section_url,False)
        if not content:
            return []

        # 提取文章链接
        links = self.get_article_links(content)
        print(f"🔗 发现 {len(links)} 篇新闻")

        # 过滤无效链接并添加域名
        articles = []
        for link in set(links):
            if link.startswith('/202'):
                full_url = f"https://edition.cnn.com{link}"
                articles.append(full_url)
        return articles

    def crawl_article(self, url):
        """爬取单篇文章"""
        time.sleep(random.uniform(*self.delay_range)) # 随机延迟
        # 给fetch_and_save添加超时参数
        # content = self.fetcher.fetch_and_save(url, False, timeout=self.request_timeout)
        content = self.fetcher.fetch_and_save(url, False)
        return Parser.parse_cnn(content, url) if content else None

    def crawl(self, max_articles=50):
        """主爬取方法"""
        all_articles = []

        # 第一步：爬取各板块获取文章链接
        for section in self.base_urls:
            all_articles.extend(self.crawl_section(section))
            if len(all_articles) >= max_articles:
                break
        # 第二步：并行爬取具体文章
        results = []
        articles_to_crawl = all_articles[:max_articles]

        # 使用线程池（控制在5个并发以内）
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.crawl_article, url): url
                for url in articles_to_crawl
            }

            for i, future in enumerate(as_completed(futures)):
                url = futures[future]
                try:
                    if article_data := future.result():
                        results.append(article_data)
                        print(f"✅ 完成文章 ({len(results)}/{len(articles_to_crawl)})：{url}")
                except Exception as e:
                    print(f"⛔ 处理失败: {url} - {str(e)}")
        # 保存结果
        if results:
            Saver.save_data(results)
            print(f"✅ 成功保存 {len(results)} 篇新闻")
        else:
            print("⚠️ 未获取到有效新闻")


class Parser:
    @staticmethod
    def parse_cnn(content,url=None):
        """解析CNN文章内容"""
        html = etree.HTML(content)
        article_data = {
            "title": "No Title",
            "url": url,
            "author": "Unknown",
            "publish_time": "",
            "content": ""
        }

        # 优先从结构化数据中提取
        ld_json = None
        scripts = html.xpath('//script[@type="application/ld+json"]/text()')
        for script in scripts:
            try:
                data = json.loads(script.strip())
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "NewsArticle":
                            ld_json = item
                            break
                elif data.get("@type") == "NewsArticle":
                    ld_json = data
                if ld_json:
                    break
            except:
                continue

        # 标题处理
        if ld_json:
            article_data["title"] = ld_json.get("headline", "").strip()
            authors = []
            if "author" in ld_json:
                auth_list = ld_json["author"] if isinstance(ld_json["author"], list) else [ld_json["author"]]
                for auth in auth_list:
                    if isinstance(auth, dict):
                        authors.append(auth.get("name", "").strip())
            article_data["author"] = ", ".join(filter(None, authors)) or "Unknown"
            article_data["publish_time"] = ld_json.get("datePublished", "").strip()
            # article_data["content"] = ld_json.get("articleBody", "").replace("\n\n", "\n").strip()

        # 降级处理：从HTML元素提取
        if not article_data["title"]:
            title_elem = html.xpath('//h1/text()')
            article_data["title"] = title_elem[0].strip() if title_elem else "No Title"

        if article_data["author"] == "Unknown":
            author_elems = html.xpath('//div[contains(@class, "byline__name")]//text()')
            authors = [a.strip() for a in author_elems if a.strip()]
            article_data["author"] = ", ".join(authors) or "Unknown"

        if not article_data["publish_time"]:
            time_elem = html.xpath('//div[contains(@class, "timestamp")]/text()')
            article_data["publish_time"] = time_elem[0].strip() if time_elem else ""

        # if not article_data["content"]:
        #     content_paras = html.xpath('//div[contains(@class, "article__content")]//p[not(@class)]//text()')
        #     article_data["content"] = "\n".join(p.strip() for p in content_paras if p.strip())
        # 强制使用HTML元素提取（保证分段）
        content_paras = []
        # 通过更精准的XPath定位段落
        para_nodes = html.xpath(
            '//div[contains(@class, "article__content")]//p[@class="paragraph inline-placeholder vossi-paragraph"]')
        for p in para_nodes:
            # 提取段落内所有文本（包括子节点）
            texts = p.xpath('.//text()')
            cleaned = ' '.join([t.strip() for t in texts if t.strip()])
            if cleaned:
                content_paras.append(cleaned)
        # 用双换行符连接段落
        article_data["content"] = '\n\n'.join(content_paras)

        return article_data
