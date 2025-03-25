from lxml import etree

class qidianSpider:
    def __init__(self):
        pass

class Parser:
    @staticmethod
    def parse_qidian(content):
        """解析起点月票榜页面"""
        html = etree.HTML(content)
        items = html.xpath('//*[@id="rank-view-list"]/div/ul/li')

        results = []
        for item in items:
            data = {
                '排名': item.xpath('.//div[@class="book-img-box"]/span/text()')[0],
                '书名': item.xpath('.//h4/a/text()')[0],
                '作者': item.xpath('.//p[@class="author"]/a[1]/text()')[0],
                '类型': item.xpath('.//p[@class="author"]/a[2]/text()')[0],
                '简介': item.xpath('.//p[@class="intro"]/text()')[0].strip(),
                '最新章节': item.xpath('.//p[@class="update"]/a/text()')[0],
                '图书链接': 'https:' + item.xpath('.//h4/a/@href')[0],
                '封面图片': 'https:' + item.xpath('.//div[@class="book-img-box"]/a/img/@src')[0]
            }
            results.append(data)
        return results