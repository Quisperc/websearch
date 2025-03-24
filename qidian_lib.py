# qidian_lib.py
import re
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from lxml import etree
import csv
import pandas as pd


class WebUtils:
    @staticmethod
    def generate_filename(url):
        """生成安全的文件名"""
        filename = re.sub(r'://', '_', url)
        filename = re.sub(r'[^\w\.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        return f"{filename or 'default'}.txt"

    @staticmethod
    def decode_content(content, response):
        """自动检测编码并解码"""
        charset = response.headers.get_content_charset()
        if not charset:
            soup = BeautifulSoup(content, 'html.parser')
            if meta := soup.find('meta', {'charset': True}):
                charset = meta['charset']
            elif (meta := soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})) \
                    and (match := re.search(r'charset=([\w-]+)', meta.get('content', ''), re.I)):
                charset = match.group(1)

        encodings = [charset] if charset else []
        encodings += ['utf-8', 'gbk', 'latin-1', 'iso-8859-1']

        for encoding in filter(None, encodings):
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode('utf-8', errors='replace')


class Fetcher:
    def __init__(self):
        self.ua = UserAgent()

    def get_random_headers(self):
        return {'User-Agent': self.ua.random}

    def fetch_and_save(self, url, save_origin=True):
        """获取并保存网页内容"""
        try:
            req = urllib.request.Request(url, headers=self.get_random_headers())
            with urllib.request.urlopen(req) as response:
                content = response.read()

                if save_origin:
                    filename = WebUtils.generate_filename(url)
                    decoded = WebUtils.decode_content(content, response)
                    with open(f'origin/{filename}', 'w', encoding='utf-8') as f:
                        f.write(decoded)
                    print(f"✅ 原始网页保存至: origin/{filename}")

                return WebUtils.decode_content(content, response)

        except urllib.error.URLError as e:
            print(f"⚠️ 连接失败: {e.reason}")
        except urllib.error.HTTPError as e:
            print(f"⛔ HTTP错误 {e.code}: {e.reason}")
        except Exception as e:
            print(f"❌ 意外错误: {str(e)}")


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


class Saver:
    @staticmethod
    def save_data(data, format_type='both'):
        """保存解析后的数据"""
        if format_type in ('csv', 'both'):
            with open('parsed/results.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

        if format_type in ('excel', 'both'):
            pd.DataFrame(data).to_excel('parsed/results.xlsx', index=False)
