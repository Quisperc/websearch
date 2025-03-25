# biqu_Spider.py
from urllib.parse import urljoin
from lxml import etree

from utils.BaseSpider import BaseSpider
from utils.TqdmLogHandler import logger


class biquSpider(BaseSpider):
    def __init__(self, config=None):
        super().__init__("22biqu", config)
        self.base_url = "https://m.22biqu.com/biqu5403/5419628.html"
        self.visited_urls = set()

    def _extract_links(self, content, current_url):
        try:
            html = etree.HTML(content)
            raw_links = html.xpath('//a[@id="pt_next"][contains(@class,"Readpage_up")]/@href')
            # logger.info(raw_links)
            return [urljoin(current_url, link) for link in raw_links]
        except Exception as e:
            logger.error(f"解析链接失败: {str(e)}")
            return []

    def _extract_article(self, content):
        try:
            html = etree.HTML(content)
            return {
                "title": html.xpath('//h1/text()')[0].strip(),
                "content": '\n'.join(html.xpath('//div[@id="chaptercontent"]//text()')),
                "url": self.current_url
            }
        except Exception as e:
            logger.error(f"解析失败: {str(e)}")
            return None

    def crawl(self, max_articles=50):
        current_url = self.base_url

        while max_articles > 0 and current_url:
            #if current_url in self.visited_urls:
            #    break

            # 获取页面内容
            content = self.fetcher.fetch_and_save(current_url, language="22biqu", save_origin=True)
            # if not content:
            #     break

            # # 提取并保存内容
            # if article := self._extract_article(content):
            #     Saver.save_data([article])
            #     max_articles -= 1
            #     logger.info(f"剩余章节数: {max_articles} | 当前章节: {article['title']}")

            # 获取下一页链接
            next_links = self._extract_links(content, current_url)
            #logger.info(next_links)
            if not next_links:
                break

            current_url = next_links[0]
            #logger.info(current_url)
            #self.visited_urls.add(current_url)
