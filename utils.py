# utils.py
import re
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed  # 确保正确导入
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from abc import ABC, abstractmethod
from threading import Lock

from bs4 import BeautifulSoup
from colorama import Fore, Style
from fake_useragent import UserAgent
import csv
import pandas as pd
from numpy import random
from tqdm import tqdm #进度条显示进度



class WebUtils:
    @staticmethod
    def generate_filename(url):
        """生成安全的文件名"""
        filename = re.sub(r'://', '_', url)
        filename = re.sub(r'[^\w\.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        filename = re.sub(r'\?', '_', filename).strip('_')
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
    def __init__(self, retries=3, timeout=10):
        self.ua = UserAgent()
        self.retries = retries
        self.timeout = timeout

    def get_random_headers(self):
        return {'User-Agent': self.ua.random}

    def fetch_and_save(self, url, language=True, save_origin=True):
        """带重试机制的请求方法"""
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, headers=self.get_random_headers())
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    content = response.read()
                    decoded = WebUtils.decode_content(content, response)

                    if save_origin:
                        self._save_origin_file(url, decoded, language)

                    return decoded
            except urllib.error.HTTPError as e:
                logger.info(f"⛔ HTTP错误 {e.code}: {e.reason} (尝试 {attempt + 1}/{self.retries})")
            except Exception as e:
                logger.info(f"⚠️ 请求失败: {str(e)} (尝试 {attempt + 1}/{self.retries})")
            time.sleep(2 ** attempt)  # 指数退避策略
        return None

    def _save_origin_file(self, url, content, language):
        """保存原始网页文件"""
        filename = WebUtils.generate_filename(url)
        # lang_dir = "Chinese" if language else "English"
        lang_dir = language
        save_path = Path("origin") / lang_dir / filename

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open('w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ 原始网页保存至: {save_path}")


class Saver:
    @staticmethod
    def save_data(data, save_dir="parsed", exclude_columns=None, format_type='both'):
        """通用数据保存方法"""
        try:
            base_dir = Path(save_dir)
            base_dir.mkdir(parents=True, exist_ok=True)

            # 保存结构化数据
            if format_type in ('csv', 'both') and data:
                csv_path = base_dir / "results.csv"
                Saver._save_csv(data, csv_path, exclude_columns)

            if format_type in ('excel', 'both') and data:
                excel_path = base_dir / "results.xlsx"
                Saver._save_excel(data, excel_path, exclude_columns)

            # 保存文本文件
            Saver._save_txt_files(data, base_dir)

        except PermissionError:
            logger.info("❌ 权限错误：请关闭已打开的结果文件")
        except Exception as e:
            logger.info(f"❌ 保存失败: {str(e)}")

    @staticmethod
    def _save_csv(data, path, exclude_columns):
        # 收集所有可能的字段（排除指定列）
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        fieldnames = [f for f in all_fields if f not in (exclude_columns or [])]
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _save_excel(data, path, exclude_columns):
        df = pd.DataFrame(data)
        df.drop(columns=exclude_columns or [], inplace=True, errors='ignore')
        df.to_excel(path, index=False)

    @staticmethod
    def _save_txt_files(data, base_dir):
        txt_dir = base_dir / "articles"
        txt_dir.mkdir(exist_ok=True)

        for item in data:
            if not item.get('title'):
                continue

            filename = f"{item['title'][:50].replace(' ', '_')}.txt"
            try:
                with (txt_dir / filename).open('w', encoding='utf-8') as f:
                    f.write(f"Title: {item.get('title', '')}\n")
                    f.write(f"Url: {item.get('url', '')}\n")
                    f.write(f"Author: {item.get('author', '')}\n")
                    f.write(f"Date: {item.get('publish_time', '')}\n\n")
                    f.write(item.get('content', ''))
            except Exception as e:
                logger.info(f"⚠️ 保存文件 {filename} 失败: {str(e)}")


class BaseSpider(ABC):
    """爬虫基类，定义通用接口"""

    def __init__(self, name, config=None):
        self.name = name
        self.config = config or {}
        self.fetcher = Fetcher(
            retries=self.config.get('retries', 3),
            timeout=self.config.get('timeout', 10)
        )
        self.delay_range = self.config.get('delay_range', (1, 3))
        self.threads = self.config.get('threads', 5)

        self.log_lock = Lock()  # 新增日志锁

    @abstractmethod
    def crawl(self):
        """子类必须实现的爬取逻辑"""
        pass

    def random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(*self.delay_range))

    def parallel_execute(self, tasks, worker):
        """通用并行执行方法"""
        results = []
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = {executor.submit(worker, task): task for task in tasks}
            # total_tasks = len(futures)
            # done_tasks = 0  # 新增计数器

            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.extend(result if isinstance(result, list) else [result])
                    # done_tasks += 1  # 每次循环递增
                    # logger.info(f"✅ 进度 ({done_tasks}/{total_tasks})")  # 使用任务数统计
                except Exception as e:
                    # done_tasks += 1  # 即使失败，任务也算完成
                    logger.error(f"⚠️ 任务执行失败: {str(e)}")
        return results

    def log(self, message, prefix="⏳"):
        """线程安全的日志输出"""
        with self.log_lock:
            tqdm.write(f"{prefix} {message}")

# utils.py
from logging import Handler, Formatter, getLogger

class TqdmLogHandler(Handler):
    """将日志消息重定向到tqdm.write"""
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)

# 配置全局logger
logger = getLogger("spider")
logger.setLevel("INFO")
handler = TqdmLogHandler()
handler.setFormatter(Formatter("%(message)s"))
logger.addHandler(handler)
