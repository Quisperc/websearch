# biqu_Spider.py
from urllib.parse import urljoin
from lxml import etree

from utils.BaseSpider import BaseSpider
from utils.TqdmLogHandler import logger


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
        super().__init__("22biqu", config)  # 继承基类配置
        self.base_url = "https://m.22biqu.com/biqu5403/5419628.html"  # 初始章节URL
        self.visited_urls = set()  # 已访问URL集合（当前未启用）

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
            html = etree.HTML(content)
            # 精准定位下一页按钮（复合选择器）
            raw_links = html.xpath('//a[@id="pt_next"][contains(@class,"Readpage_up")]/@href')
            # 生成绝对URL（处理分页参数）
            return [urljoin(current_url, link) for link in raw_links]
        except Exception as e:
            logger.error(f"解析链接失败: {str(e)}")
            return []

    def _extract_article(self, content):
        """解析单章小说内容

        提取规则：
        - 标题从h1标签直接获取
        - 正文内容合并所有文本节点
        - 保留当前URL作为数据溯源

        Args:
            content (str): 章节页面HTML内容

        Returns:
            dict/None: 包含标题、内容等字段的字典，解析失败返回None
        """
        try:
            html = etree.HTML(content)
            return {
                "title": html.xpath('//h1/text()')[0].strip(),  # 标题必填项
                "content": '\n'.join(
                    html.xpath('//div[@id="chaptercontent"]//text()')  # 合并所有文本节点
                ).strip(),
                "url": self.current_url  # 记录数据来源
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
        current_url = self.base_url

        while max_articles > 0 and current_url:
            # 防重复机制（当前注释状态，需要时可启用）
            # if current_url in self.visited_urls:
            #     break

            # 获取并缓存原始页面
            content = self.fetcher.fetch_and_save(current_url, language="22biqu", save_origin=True)

            # 数据保存逻辑（当前注释状态，按需启用）
            # if article := self._extract_article(content):
            #     Saver.save_data([article])
            #     max_articles -= 1
            #     logger.info(f"剩余章节数: {max_articles} | 当前章节: {article['title']}")

            # 获取下一页链接（通常包含0-1个元素）
            next_links = self._extract_links(content, current_url)
            if not next_links:
                logger.info("🛑 已到达最终章节")
                break

            # 更新当前URL（实现链式跳转）
            current_url = next_links[0]
            # self.visited_urls.add(current_url)  # 去重机制（需配合启用防重复判断）
