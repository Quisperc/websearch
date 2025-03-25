# Fetcher.py
import time
from pathlib import Path

from fake_useragent import UserAgent
import urllib.request
import urllib.error

from utils.TqdmLogHandler import logger
from utils.WebUtils import WebUtils


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
        save_path = Path("../origin") / lang_dir / filename

        save_path.parent.mkdir(parents=True, exist_ok=True)
        with save_path.open('w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"✅ 原始网页保存至: {save_path}")