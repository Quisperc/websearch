from bs4 import BeautifulSoup

from base_spider import BaseSpider


class NovelSpider(BaseSpider):
    def __init__(self):
        super().__init__("Novel", 'zh', {'delay_range': (1, 3), 'max_workers': 5})
        self.base_template = "https://www.kuaishu5.com/b121721/{}.html"

    def start_requests(self):
        return [self.base_template.format(i) for i in range(27710, 27712)]

    def extract_links(self, content, url):
        return []

    def parse(self, content, url):
        # 示例解析逻辑，需根据实际网页结构调整
        return {
            'title': url.split('/')[-1],
            'url': url,
            'author': '佚名',
            'publish_time': '2023',
            'content': '\n'.join(BeautifulSoup(content, 'html.parser').stripped_strings)
        }
