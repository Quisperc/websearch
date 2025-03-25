from lxml import etree
import json

from base_spider import BaseSpider


class CNNSpider(BaseSpider):
    def __init__(self):
        super().__init__("CNN", 'en', {'delay_range': (1, 3), 'max_workers': 5})
        self.base_urls = [
            "https://edition.cnn.com/world",
            "https://edition.cnn.com/politics",
            "https://edition.cnn.com/business",
            "https://edition.cnn.com/tech"
        ]

    def start_requests(self):
        return self.base_urls

    def extract_links(self, content, url):
        html = etree.HTML(content)
        return html.xpath('//a[contains(@href, "/202")]/@href')

    def parse(self, content, url):
        html = etree.HTML(content)
        article = {'url': url, 'title': '', 'author': '', 'publish_time': '', 'content': ''}

        # 结构化数据解析
        scripts = html.xpath('//script[@type="application/ld+json"]/text()')
        for script in scripts:
            try:
                data = json.loads(script.strip())
                if isinstance(data, list):
                    data = next((item for item in data if item.get("@type") == "NewsArticle"), {})
                if data.get("@type") == "NewsArticle":
                    article['title'] = data.get("headline", "")
                    article['publish_time'] = data.get("datePublished", "")
                    authors = [auth.get("name", "") for auth in data.get("author", []) if isinstance(auth, dict)]
                    article['author'] = ", ".join(authors) if authors else "Unknown"
                    break
            except:
                continue

        # HTML降级解析
        if not article['title']:
            article['title'] = html.xpath('//h1/text()')[0].strip() if html.xpath('//h1') else "No Title"
        # article['content'] = "\n".join(
        #     p.xpath('string()').strip()
        #     for p in html.xpath('//div[contains(@class, "article__content")]//p[not(@class)]')
        # )
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
        article["content"] = '\n\n'.join(content_paras)
        return article
