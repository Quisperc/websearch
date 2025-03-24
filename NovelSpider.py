from utils import Fetcher, Saver


class NovelSpider:
    def __init__(self):
        self.base_url = "https://www.kuaishu5.com/b121721/{}.html"
        self.fetcher = Fetcher()
        self.delay_range = (1, 3)  # 随机延迟范围

    def crawl(self, pages=27870):
        """执行爬取任务"""
        all_results = []

        for page in range(27710, pages + 1):
            url = self.base_url.format(page)
            print(f"🕸️ 正在爬取第 {page} 页: {url}")

            # 获取并保存原始网页
            content = self.fetcher.fetch_and_save(url)

            # if content:
            #     # 解析内容
            #     page_data = Parser.parse_qidian(content)
            #     all_results.extend(page_data)
            #     print(f"✅ 第 {page} 页解析完成，共 {len(page_data)} 条数据")

        # 保存结构化数据
        if all_results:
            Saver.save_data(all_results)
            print(f"💾 数据已保存至 parsed/ 目录")
        else:
            print("⚠️ 未获取到有效数据")