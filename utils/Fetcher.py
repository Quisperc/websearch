# Fetcher.py
import time
from pathlib import Path

from fake_useragent import UserAgent
import urllib.request
import urllib.error

from numpy import random

from utils.TqdmLogHandler import logger
from utils.WebUtils import WebUtils


class Fetcher:
    """HTTP请求处理器（支持重试机制和文件保存）

    核心功能：
    - 自动生成随机请求头
    - 带指数退避的重试机制
    - 内容解码自动处理
    - 原始网页存档

    典型配置参数：
    - retries: 失败请求重试次数（默认3次）
    - timeout: 请求超时时间（默认10秒）
    """

    def __init__(self, retries=3, timeout=10):
        """初始化请求器

        Args:
            retries (int): 失败请求重试次数（建议3-5次）
            timeout (int): 连接超时时间（秒，建议10-30秒）
        """
        self.ua = UserAgent()  # 随机UA生成器
        self.retries = retries
        self.timeout = timeout

    def get_random_headers(self):
        """生成随机请求头（反反爬虫基础措施）

        返回：
            dict: 包含随机User-Agent的请求头
        """
        return {'User-Agent': self.ua.random}

    def fetch_and_save(self, url, file_name=None, direction=True, save_origin=True):
        """执行请求并保存网页内容（核心方法）

        流程：
        1. 生成随机请求头
        2. 执行HTTP请求（支持重试）
        3. 解码响应内容
        4. 选择性保存原始文件

        Args:
            url (str): 目标URL
            file_name(str): 保存的文件名
            direction (bool/str): 语言标识（用于文件分类）
            save_origin (bool): 是否保存原始内容

        Returns:
            str: 解码后的网页内容，失败返回None
        """
        for attempt in range(self.retries):
            try:
                # 构造请求对象（使用随机UA）
                req = urllib.request.Request(url, headers=self.get_random_headers())

                # 发送请求（带超时控制）
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    content = response.read()

                    # 智能解码内容（自动检测编码）
                    decoded = WebUtils.decode_content(content, response)

                    # 保存原始文件（需开启save_origin）
                    if save_origin:
                        self._save_origin_file(url, decoded, direction, file_name)

                    return decoded

            except urllib.error.HTTPError as e:
                logger.info(f"⛔ HTTP错误 {e.code}: {e.reason} (尝试 {attempt + 1}/{self.retries})")
            except Exception as e:
                logger.info(f"⚠️ 请求失败: {str(e)} (尝试 {attempt + 1}/{self.retries})")

            # 指数退避策略（2^attempt秒）
            time.sleep(2 ** attempt)

        return None

    def _save_origin_file(self, url, content, direction,file_name=None):
        """保存原始网页到本地（内部方法）

        文件路径结构：
        ../origin/{language}/文件名

        Args:
            url (str): 原始URL（用于生成文件名）
            content (str): 要保存的内容
            direction (str): 分类目录名
        """
        if file_name is None:
            # 生成安全文件名（去除特殊字符）
            filename = WebUtils.generate_filename(url)
        else:
            filename = file_name

        # 构建存储路径
        lang_dir = direction if isinstance(direction, str) else "common"
        save_path = Path("origin") / lang_dir / filename

        # 创建目录（递归创建缺失目录）
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件（UTF-8编码）
        with save_path.open('w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"✅ 原始网页保存至: {save_path}")
