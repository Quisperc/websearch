from cnn_spider import CNNSpider
from novel_spider import NovelSpider
import os

if __name__ == "__main__":
    os.makedirs('../origin/Chinese', exist_ok=True)
    os.makedirs('../origin/English', exist_ok=True)
    os.makedirs('../parsed', exist_ok=True)

    # 运行小说爬虫
    novel_spider = NovelSpider()
    novel_spider.crawl()

    # 运行CNN爬虫
    cnn_spider = CNNSpider()
    cnn_spider.crawl(max_items=5)

    print("🎉 所有爬虫任务完成！")
