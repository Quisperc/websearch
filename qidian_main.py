# qidian_main.py
from qidian_lib import Fetcher, Parser, Saver


class QiDianSpider:
    def __init__(self):
        self.base_url = "https://www.qidian.com/rank/yuepiao?chn=-1&page={}"
        self.fetcher = Fetcher()

    def crawl(self, pages=5):
        """执行爬取任务"""
        all_results = []

        for page in range(1, pages + 1):
            url = self.base_url.format(page)
            print(f"🕸️ 正在爬取第 {page} 页: {url}")

            # 获取并保存原始网页
            # 测试 保存原文件是否可用
            url = "http://jwc.swjtu.edu.cn"
            content = self.fetcher.fetch_and_save(url)

            if content:
                # 解析内容
                page_data = Parser.parse_qidian(content)
                all_results.extend(page_data)
                print(f"✅ 第 {page} 页解析完成，共 {len(page_data)} 条数据")

        # 保存结构化数据
        if all_results:
            Saver.save_data(all_results)
            print(f"💾 数据已保存至 parsed/ 目录")
        else:
            print("⚠️ 未获取到有效数据")


if __name__ == "__main__":
    import os

    # 创建存储目录
    os.makedirs('origin', exist_ok=True)
    os.makedirs('parsed', exist_ok=True)

    spider = QiDianSpider()
    spider.crawl(pages=5)
    print("🎉 所有任务已完成！")
