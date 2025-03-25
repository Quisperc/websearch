# BaseSpider.py
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from numpy import random
from tqdm import tqdm

from utils.Fetcher import Fetcher
from utils.TqdmLogHandler import logger


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