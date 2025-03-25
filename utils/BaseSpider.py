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
    """爬虫基类，定义通用接口和基础功能

    特性：
    - 多线程并发执行
    - 自动重试机制
    - 随机请求延迟
    - 线程安全日志
    - 可扩展的配置参数

    典型配置参数（可通过config字典覆盖）：
    - retries: 请求重试次数（默认3次，建议2-5）
    - timeout: 请求超时时间（默认10秒，建议10-30）
    - delay_range: 随机延迟范围（默认1-3秒，高频率请求建议3-5秒）
    - threads: 并发线程数（默认5，根据目标网站承受能力调整）
    """

    def __init__(self, name, config=None):
        """初始化爬虫实例

        Args:
            name (str): 爬虫名称，用于日志标识
            config (dict): 配置字典，支持覆盖默认参数：
                - retries: 请求失败重试次数
                - timeout: 请求超时时间(秒)
                - delay_range: (min, max)随机延迟范围
                - threads: 最大并发线程数
        """
        self.name = name
        self.config = config or {}

        # 初始化请求器（配置重试和超时）
        self.fetcher = Fetcher(
            retries=self.config.get('retries', 3),  # 默认3次重试
            timeout=self.config.get('timeout', 10)  # 默认10秒超时
        )

        # 请求延迟配置（防止IP封锁）
        self.delay_range = self.config.get('delay_range', (1, 3))  # 默认1-3秒随机延迟

        # 并发执行配置（根据目标网站承受能力调整）
        self.threads = self.config.get('threads', 5)  # 默认5线程并发

        # 线程安全日志锁（防止多线程日志输出混乱）
        self.log_lock = Lock()

    @abstractmethod
    def crawl(self):
        """子类必须实现的爬取逻辑（抽象方法）

        实现要求：
        - 定义具体的爬取流程
        - 调用parallel_execute进行并发处理
        - 返回结构化数据或保存结果
        """
        pass

    def random_delay(self):
        """执行随机延迟（遵守爬虫礼仪）

        使用numpy生成均匀分布的随机延迟，比标准random更高效
        建议根据目标网站robots.txt要求调整延迟范围
        """
        time.sleep(random.uniform(*self.delay_range))

    def parallel_execute(self, tasks, worker):
        """通用并行执行方法（生产者-消费者模式）

        参数：
        - tasks (iterable): 任务列表（如URL列表）
        - worker (callable): 任务处理函数，接收单个task作为参数

        返回：
        list: 所有worker返回结果的集合（自动展开列表型结果）

        设计特点：
        - 使用ThreadPoolExecutor管理线程池
        - 支持动态任务提交和结果收集
        - 自动处理任务异常并记录错误日志
        """
        results = []
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            # 提交初始任务集合（future->task映射用于错误追踪）
            futures = {executor.submit(worker, task): task for task in tasks}

            # 使用tqdm进度条（需配合适当的total参数）
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        # 自动展开列表型结果（支持多维结果收集）
                        results.extend(result if isinstance(result, list) else [result])
                except Exception as e:
                    task = futures[future]
                    logger.error(f"⚠️ 任务执行失败: {task} - {str(e)}")
        return results

    def log(self, message, prefix="⏳"):
        """线程安全的日志输出方法

        参数：
        - message (str): 日志消息内容
        - prefix (str): 状态标识符号（默认⏳，可选✅⚠️❌）

        设计特点：
        - 使用tqdm.write避免打断进度条
        - 使用Lock确保多线程日志完整性
        - 支持带状态标识的结构化日志
        """
        with self.log_lock:
            tqdm.write(f"{prefix} {self.name} - {message}")
