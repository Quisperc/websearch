# utils.py
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
        """生成安全的文件名"""
        filename = re.sub(r'://', '_', url)
        filename = re.sub(r'[^\w\.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        return f"{filename or 'default'}.html"

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

    # 生成随机用户
    def get_random_headers(self):
        return {'User-Agent': self.ua.random}

    # 获取并保存网页内容
    def fetch_and_save(self, url, language=True, save_origin=True):
        """获取并保存网页内容"""
        try:
            req = urllib.request.Request(url, headers=self.get_random_headers())
            with urllib.request.urlopen(req) as response:
                content = response.read()

                if save_origin:
                    filename = WebUtils.generate_filename(url)
                    decoded = WebUtils.decode_content(content, response)
                    if language:
                        with open(f'origin/Chinese/{filename}', 'w', encoding='utf-8') as f:
                            f.write(decoded)
                        print(f"✅ 原始网页保存至: origin/Chinese/{filename}")
                    else:
                        with open(f'origin/English/{filename}', 'w', encoding='utf-8') as f:
                            f.write(decoded)
                        print(f"✅ 原始网页保存至: origin/English/{filename}")

                return WebUtils.decode_content(content, response)

        except urllib.error.HTTPError as e:
            print(f"⛔ HTTP错误 {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            print(f"⚠️ 连接失败: {e.reason}")
        except Exception as e:
            print(f"❌ 意外错误: {str(e)}")


class Saver:
    @staticmethod
    def save_data(data,exclude_columns=None, format_type='both'):
        """安全保存解析数据"""
        try:
            # 确保目录存在
            save_dir = Path("../parsed")
            save_dir.mkdir(exist_ok=True, parents=True)

            # 统一文件名处理
            def safe_filename(title):
                return "".join([c if c.isalnum() else "_" for c in title[:50]]).rstrip()

            # 保存CSV和Excel
            if format_type in ('csv', 'both') and data:
                csv_path = save_dir / "results.csv"
                with csv_path.open('w', newline='', encoding='utf-8') as f:
                    # writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    # 生成排除后的字段列表
                    fieldnames = [key for key in data[0].keys() if key not in exclude_columns]
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(data)
            if format_type in ('excel', 'both') and data:
                # pd.DataFrame(data).to_excel(save_dir / "results.xlsx", index=False)
                df = pd.DataFrame(data)
                # 删除指定列（忽略不存在的情况）
                df.drop(columns=exclude_columns, inplace=True, errors='ignore')
                df.to_excel(save_dir / "results.xlsx", index=False)

            # 保存TXT文件到子目录
            txt_dir = save_dir / "articles"
            txt_dir.mkdir(exist_ok=True)
            for article in data:
                if not article.get('title'):
                    continue

                filename = safe_filename(article['title']) + ".txt"
                try:
                    with (txt_dir / filename).open('w', encoding='utf-8') as f:
                        f.write(f"Title: {article.get('title', '')}\n")
                        f.write(f"Url: {article.get('url', '')}\n")
                        f.write(f"Author: {article.get('author', '')}\n")
                        f.write(f"Date: {article.get('publish_time', '')}\n")
                        f.write("\nContent:\n")
                        f.write(article.get('content', ''))
                except Exception as e:
                    print(f"⚠️ 保存文件 {filename} 失败: {str(e)}")
        except PermissionError:
            print("❌ 权限错误：请关闭已打开的结果文件")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")