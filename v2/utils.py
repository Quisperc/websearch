import re
import urllib.request
import urllib.error
from pathlib import Path
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import csv
import pandas as pd


class WebUtils:
    @staticmethod
    def generate_filename(url):
        filename = re.sub(r'://', '_', url)
        filename = re.sub(r'[^\w\.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        return f"{filename or 'default'}.html"

    @staticmethod
    def decode_content(content, response):
        charset = response.headers.get_content_charset()
        if not charset:
            soup = BeautifulSoup(content, 'html.parser')
            if meta := soup.find('meta', {'charset': True}):
                charset = meta['charset']
            elif (meta := soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})) \
                    and (match := re.search(r'charset=([\w-]+)', meta.get('content', ''), re.I)):
                charset = match.group(1)
        encodings = [charset] if charset else ['utf-8', 'gbk', 'latin-1']
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

    def fetch_and_save(self, url, language=True, save_origin=True):
        try:
            req = urllib.request.Request(url, headers=self.get_random_headers())
            with urllib.request.urlopen(req) as response:
                content = response.read()
                if save_origin:
                    filename = WebUtils.generate_filename(url)
                    decoded = WebUtils.decode_content(content, response)
                    lang_dir = 'Chinese' if language else 'English'
                    save_path = Path('../origin') / lang_dir / filename
                    with save_path.open('w', encoding='utf-8') as f:
                        f.write(decoded)
                    print(f"✅ 原始网页保存至: {save_path}")
                return decoded
        except Exception as e:
            print(f"抓取失败 {url}: {e}")
            return None


class Saver:
    @staticmethod
    def save_data(data, subdir=None, exclude_columns=None, format_type='both'):
        try:
            save_dir = Path("../parsed") / subdir if subdir else Path("../parsed")
            save_dir.mkdir(exist_ok=True, parents=True)

            def safe_filename(title):
                return "".join([c if c.isalnum() else "_" for c in str(title)[:50]]).rstrip()

            # 保存结构化数据
            if format_type in ('csv', 'both') and data:
                csv_path = save_dir / "results.csv"
                fieldnames = [key for key in data[0].keys() if key not in (exclude_columns or [])]
                with csv_path.open('w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)

            if format_type in ('excel', 'both') and data:
                df = pd.DataFrame(data).drop(columns=exclude_columns or [], errors='ignore')
                df.to_excel(save_dir / "results.xlsx", index=False)

            # 保存文本内容
            txt_dir = save_dir / "articles"
            txt_dir.mkdir(exist_ok=True)
            for item in data:
                if not item.get('title'):
                    continue
                filename = safe_filename(item['title']) + ".txt"
                try:
                    with (txt_dir / filename).open('w', encoding='utf-8') as f:
                        f.write(f"标题: {item.get('title', '')}\n")
                        f.write(f"链接: {item.get('url', '')}\n")
                        f.write(f"作者: {item.get('author', '')}\n")
                        f.write(f"日期: {item.get('publish_time', '')}\n\n")
                        f.write(item.get('content', ''))
                except Exception as e:
                    print(f"保存失败 {filename}: {e}")
        except Exception as e:
            print(f"保存数据时出错: {e}")
