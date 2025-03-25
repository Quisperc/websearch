import concurrent.futures
import random
import time

from utils import Saver, Fetcher


class NovelSpider:
    def __init__(self):
        self.base_url = "https://www.kuaishu5.com/b121721/{}.html"
        self.fetcher = Fetcher()
        self.delay_range = (1, 3)  # 随机延迟范围

    def _crawl_single_page(self, page):
        """处理单个页面爬取的内部方法"""
        try:
            # 随机延迟防止被封
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)

            url = self.base_url.format(page)
            print(f"🕸️ 正在爬取第 {page} 页: {url}")

            # 获取网页内容（自动保存原始文件）
            content = self.fetcher.fetch_and_save(url, language=True)

            # if content:
            #     # 解析网页内容（需实现解析逻辑）
            #     page_data = Parser.parse_qidian(content)
            #     print(f"✅ 第 {page} 页解析完成，共 {len(page_data)} 条数据")
            #     return page_data
            return []  # 暂时返回空数据

        except Exception as e:
            print(f"⚠️ 第 {page} 页爬取失败: {str(e)}")
            return []

    def crawl(self, pages=27870):
        """执行并行爬取任务"""
        all_results = []
        start_page = 27710

        # 创建线程池（建议 5-10 个线程）
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # 生成所有页面任务
            future_to_page = {
                executor.submit(self._crawl_single_page, page): page
                for page in range(start_page, pages + 1)
            }

            # 实时获取完成的任务
            for future in concurrent.futures.as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    page_data = future.result()
                    all_results.extend(page_data)
                except Exception as e:
                    print(f"⚠️ 第 {page} 页出现异常: {str(e)}")

        # 保存所有解析结果
        if all_results:
            # TODO 解析小说
            # Saver.save_data(all_results)
            print(f"💾 数据已保存至 parsed/ 目录")
        else:
            print("⚠️ 未获取到有效数据")
