# cnn_spider.py （分类过于麻烦，已弃用）
import json

from lxml import etree

from utils.BaseSpider import BaseSpider
from utils.Saver import Saver
from utils.TqdmLogHandler import logger


class CNNSpider(BaseSpider):
    """CNN新闻爬虫

    核心功能：
    - 多频道并行爬取（国际/政治/商业/科技等9个板块）
    - 双阶段采集流程（链接收集 + 内容抓取）
    - 结构化数据优先解析（JSON-LD）
    - HTML降级解析策略
    - 智能去重与结果持久化

    设计特点：
    - 继承BaseSpider基类实现定制逻辑
    - 支持随机延迟防封禁
    - 自动编码处理与内容缓存
    - 进度可视化与异常捕获
    """

    def __init__(self, config=None):
        """初始化爬虫实例

        Args:
            config (dict, optional): 爬虫配置参数，可覆盖默认设置
        """
        super().__init__("cnn", config)  # 继承基类初始化逻辑
        # CNN各频道入口URL列表
        self.base_urls = [
            "https://edition.cnn.com/world",  # 国际新闻
            "https://edition.cnn.com/politics",  # 政治新闻
            "https://edition.cnn.com/business",  # 商业新闻
            "https://edition.cnn.com/tech",  # 科技新闻
            "https://edition.cnn.com/health",  # 健康新闻
            "https://edition.cnn.com/entertainment",  # 娱乐新闻
            "https://edition.cnn.com/us",  # 美国新闻
            "https://edition.cnn.com/travel",  # 旅游新闻
            "https://edition.cnn.com/style",  # 时尚新闻
        ]

    def crawl(self, max_articles=50):
        """主爬取控制流程

        执行步骤：
        1. 并行爬取各板块获取文章链接
        2. 链接去重与数量控制
        3. 并行爬取文章详情内容
        4. 结果持久化存储

        Args:
            max_articles (int): 最大抓取数量，默认50篇
        """
        # 第一阶段：分布式收集文章链接
        article_urls = self.parallel_execute(self.base_urls, self._crawl_section)
        article_urls = list(set(article_urls))[:max_articles]  # 去重+数量控制
        logger.info(f"🔗 总共 {len(article_urls)} 篇新闻")

        # 第二阶段：并行获取文章内容
        articles = self.parallel_execute(article_urls, self._crawl_article)

        # 数据持久化
        if articles:
            self._save_results(articles)
            logger.info(f"✅ 成功保存 {len(articles)} 篇CNN新闻")
        else:
            logger.info("⚠️ 未获取到有效新闻")

    def _crawl_section(self, url):
        """爬取新闻板块页面

        执行步骤：
        - 获取并缓存页面内容
        - 提取有效文章链接
        - 记录采集状态

        Args:
            url (str): 板块入口URL

        Returns:
            list: 本板块提取到的文章链接列表
        """
        logger.info(f"⏳ 开始爬取板块: {url}")
        content = self.fetcher.fetch_and_save(url, direction="CNN")  # 带自动缓存的请求

        # 内容有效性校验
        if not content:
            return []

        # 提取并返回文章链接（带日志记录）
        links = self._extract_links(content)
        logger.info(f"🔗 发现 {len(links)} 篇新闻")
        return links

    def _extract_links(self, content):
        """从HTML中精准提取文章链接

        改进点：
        - 增强XPath选择器准确性
        - 添加路径深度校验
        - 加入异常处理机制

        Args:
            content (str): HTML内容

        Returns:
            list: 标准化后的完整文章URL列表
        """
        try:
            html = etree.HTML(content)
            # 宽松匹配可能包含文章的链接
            raw_links = html.xpath('//a[contains(@href, "/20")]/@href')  # 包含年份的路径

            # 过滤规则：
            # 1. 路径以/202开头（CNN文章路径特征）
            # 2. 路径段数大于3（排除简单页面）
            valid_links = {
                link for link in raw_links
                if link.startswith('/202') and len(link.split('/')) > 3
            }
            # 生成完整URL并返回
            return [f"https://edition.cnn.com{link}" for link in valid_links]
        except Exception as e:
            logger.error(f"解析链接失败: {str(e)}")
            return []

    def _crawl_article(self, url):
        """爬取单篇文章详情

        执行步骤：
        - 随机延迟（反爬策略）
        - 获取并缓存原始页面
        - 解析结构化数据

        Args:
            url (str): 文章详情页URL

        Returns:
            dict/None: 解析成功的文章数据，失败返回None
        """
        self.random_delay()  # 随机延迟（继承自BaseSpider）
        logger.info(f"⏳ 开始爬取文章: {url}")

        content = self.fetcher.fetch_and_save(url, direction="CNN", save_origin=True)
        return self._parse_article(content, url) if content else None

    def _parse_article(self, content, url):
        """解析文章内容（结构化优先，降级解析）

        解析策略：
        1. 优先从JSON-LD获取结构化数据
        2. 失败时降级使用XPath提取
        3. 内容段落智能合并

        Args:
            content (str): HTML内容
            url (str): 当前文章URL

        Returns:
            dict: 包含标题、作者等字段的文章数据字典
        """
        html = etree.HTML(content)
        article = {
            "title": "No Title",
            "url": url,
            "author": "Unknown",
            "publish_time": "",
            "content": ""
        }

        # 第一优先级：结构化数据（Schema.org）
        ld_json = self._extract_json_ld(html)
        if ld_json:
            article.update({
                "title": ld_json.get("headline", "").strip(),
                "author": self._parse_authors(ld_json.get("author", [])),
                "publish_time": ld_json.get("datePublished", "").strip()
            })

        # 第二优先级：HTML原生解析
        if not article["title"]:
            title_nodes = html.xpath('//h1/text()')
            article["title"] = title_nodes[0].strip() if title_nodes else "No Title"

        # 内容提取策略
        content_paragraphs = [
            ' '.join(p.xpath('.//text()')).strip()  # 合并段落内所有文本节点
            for p in html.xpath('//div[contains(@class, "article__content")]//p')
            if p.xpath('.//text()')  # 过滤空段落
        ]
        article["content"] = "\n\n".join(content_paragraphs)

        return article

    def _extract_json_ld(self, html):
        """提取JSON-LD结构化数据

        JSON-LD说明：
        - 网站使用的结构化数据格式
        - 包含文章标题、作者等元数据
        - 可能为单个对象或对象数组

        Args:
            html (etree.Element): 解析后的HTML树

        Returns:
            dict/None: 成功解析的NewsArticle数据，失败返回None
        """
        for script in html.xpath('//script[@type="application/ld+json"]/text()'):
            try:
                data = json.loads(script.strip())
                # 处理数组形式的JSON-LD
                if isinstance(data, list):
                    data = next((item for item in data if item.get("@type") == "NewsArticle"), None)
                # 验证数据有效性
                if data and data.get("@type") == "NewsArticle":
                    return data
            except json.JSONDecodeError:
                continue  # 跳过格式错误的JSON
        return None

    def _parse_authors(self, authors):
        """解析作者信息

        处理多种数据格式：
        - 单个作者对象：{"name": "xxx"}
        - 作者数组：[{"name": "xxx"}, ...]
        - 字符串格式："name"

        Args:
            authors (dict/list/str): 原始作者数据

        Returns:
            str: 逗号分隔的作者名字符串
        """
        # 统一数据格式为列表
        if isinstance(authors, dict):
            authors = [authors]

        return ", ".join([
            auth.get("name", "").strip()
            for auth in authors
            if isinstance(auth, dict)  # 过滤无效数据
        ]) or "Unknown"  # 空值保护

    def _save_results(self, data):
        """持久化存储解析结果

        存储策略：
        - 保存到parsed/cnn目录
        - 同时生成CSV和JSON文件
        - 排除大文本字段（content）的CSV输出

        Args:
            data (list): 文章数据字典列表
        """
        Saver.save_data(
            data,
            save_dir=f"parsed/{self.name}",  # 按爬虫名称分目录
            exclude_columns=['content'],  # CSV排除长文本
            format_type='both'  # 同时生成csv和json
        )
