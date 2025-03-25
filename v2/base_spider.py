import concurrent.futures
import random
import time
from urllib.parse import urljoin
from collections import deque
from lxml import etree

from utils import Fetcher, Saver


class BaseSpider:
    def __init__(self, name, language='en', config=None):
        self.name = name
        self.language = language
        self.config = config or {}
        self.fetcher = Fetcher()
        self.delay_range = self.config.get('delay_range', (1, 3))
        self.max_workers = self.config.get('max_workers', 5)
        self.visited = set()
        self.data = []
        self.queue = deque()

    def start_requests(self):
        raise NotImplementedError("必须实现start_requests方法")

    def extract_links(self, content, url):
        raise NotImplementedError("必须实现extract_links方法")

    def parse(self, content, url):
        raise NotImplementedError("必须实现parse方法")

    def crawl(self, max_items=None):
        self.queue.extend(self.start_requests())
        self.visited.update(self.queue)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while self.queue:
                batch = list(self.queue)
                self.queue.clear()
                futures = {executor.submit(self.process_url, url): url for url in batch}

                for future in concurrent.futures.as_completed(futures):
                    url = futures[future]
                    try:
                        new_links, item = future.result()
                        if item:
                            self.data.append(item)
                        for link in new_links:
                            if link not in self.visited and link not in self.queue:
                                self.visited.add(link)
                                self.queue.append(link)
                                if max_items and len(self.data) >= max_items:
                                    self.queue.clear()
                                    break
                    except Exception as e:
                        print(f"处理失败 {url}: {e}")

        if self.data:
            Saver.save_data(self.data, subdir=self.name)
            print(f"✅ {self.name} 保存 {len(self.data)} 条数据")
        else:
            print(f"⚠️ {self.name} 未获取数据")

    def process_url(self, url):
        time.sleep(random.uniform(*self.delay_range))
        content = self.fetcher.fetch_and_save(url, self.language == 'zh')
        if not content:
            return [], None
        new_links = [urljoin(url, link) for link in self.extract_links(content, url)]
        item = self.parse(content, url)
        return new_links, item
