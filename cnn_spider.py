# cnn_spider.py
import json
from lxml import etree
from utils import BaseSpider, Saver, logger


class CNNSpider(BaseSpider):
    """CNN新闻爬虫"""

    def __init__(self, config=None):
        super().__init__("cnn", config)
        self.base_urls = [
            "https://edition.cnn.com/world",
            "https://edition.cnn.com/politics",
            "https://edition.cnn.com/business",
            "https://edition.cnn.com/tech",
            "https://edition.cnn.com/health",
            "https://edition.cnn.com/entertainment",
            "https://edition.cnn.com/us",
            "https://edition.cnn.com/travel",
            "https://edition.cnn.com/style",
        ]

    def crawl(self, max_articles=50):
        """主爬取流程"""
        # 第一阶段：收集文章链接
        article_urls = self.parallel_execute(self.base_urls, self._crawl_section)
        article_urls = list(set(article_urls))[:max_articles]
        logger.info(f"🔗 总共 {len(article_urls)} 篇新闻")

        # 第二阶段：爬取文章内容
        articles = self.parallel_execute(article_urls, self._crawl_article)

        # 保存结果
        if articles:
            self._save_results(articles)
            logger.info(f"✅ 成功保存 {len(articles)} 篇CNN新闻")
        else:
            logger.info("⚠️ 未获取到有效新闻")

    def _crawl_section(self, url):
        """爬取板块页面"""
        logger.info(f"⏳ 开始爬取板块: {url}")
        content = self.fetcher.fetch_and_save(url, language="CNN")
        # 提取文章链接
        if not content:
            return []
        # 先提取链接再记录数量
        links = self._extract_links(content)
        logger.info(f"🔗 发现 {len(links)} 篇新闻")
        return self._extract_links(content) if content else []

    # def _extract_links(self, content):
    #     """从HTML中提取文章链接"""
    #     html = etree.HTML(content)
    #     return [
    #         f"https://edition.cnn.com{link}"
    #         for link in html.xpath('//a[contains(@href, "/202")]/@href')
    #         if link.startswith('/202')
    #     ]
    def _extract_links(self, content):
        """从HTML中提取文章链接（改进版）"""
        try:
            html = etree.HTML(content)
            # 更精准的XPath匹配，示例：匹配包含日期格式的路径
            raw_links = html.xpath('//a[contains(@href, "/20")]/@href')  # 调整XPath逻辑
            # 过滤有效链接并去重
            valid_links = {
                link for link in raw_links
                if link.startswith('/202') and len(link.split('/')) > 3  # 简单校验路径深度
            }
            return [f"https://edition.cnn.com{link}" for link in valid_links]
        except Exception as e:
            logger.error(f"解析链接失败: {str(e)}")
            return []

    def _crawl_article(self, url):
        """爬取单篇文章"""
        self.random_delay()
        logger.info(f"⏳ 开始爬取文章: {url}")

        content = self.fetcher.fetch_and_save(url, language="CNN", save_origin=True)
        return self._parse_article(content, url) if content else None

    def _parse_article(self, content, url):
        """解析文章内容"""
        html = etree.HTML(content)
        article = {
            "title": "No Title",
            "url": url,
            "author": "Unknown",
            "publish_time": "",
            "content": ""
        }

        # 从JSON-LD提取结构化数据
        ld_json = self._extract_json_ld(html)
        if ld_json:
            article.update({
                "title": ld_json.get("headline", "").strip(),
                "author": self._parse_authors(ld_json.get("author", [])),
                "publish_time": ld_json.get("datePublished", "").strip()
            })

        # HTML降级解析
        article["title"] = html.xpath('//h1/text()')[0].strip() if not article["title"] else article["title"]
        article["content"] = "\n\n".join([
            ' '.join(p.xpath('.//text()')).strip()
            for p in html.xpath('//div[contains(@class, "article__content")]//p')
        ])
        return article

    def _extract_json_ld(self, html):
        """提取结构化数据"""
        for script in html.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                data = json.loads(script.strip())
                if isinstance(data, list):
                    data = next((item for item in data if item.get("@type") == "NewsArticle"), None)
                if data and data.get("@type") == "NewsArticle":
                    return data
            except json.JSONDecodeError:
                continue
        return None

    def _parse_authors(self, authors):
        """解析作者信息"""
        if isinstance(authors, dict):
            authors = [authors]
        return ", ".join([
            auth.get("name", "").strip()
            for auth in authors
            if isinstance(auth, dict)
        ]) or "Unknown"

    def _save_results(self, data):
        """保存解析结果"""
        Saver.save_data(
            data,
            save_dir=f"parsed/{self.name}",
            # exclude_columns=['raw_content'],
            exclude_columns="content",
            format_type='both'
        )
