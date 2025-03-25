# crawler.py
from utils import Fetcher, Saver
from CNNSpider import CNNSpider
from NovelSpider import NovelSpider

if __name__ == "__main__":
    import os

    # 创建存储目录
    os.makedirs('origin', exist_ok=True)
    os.makedirs('parsed', exist_ok=True)
    # 创建存储目录
    os.makedirs('origin/Chinese', exist_ok=True)
    os.makedirs('origin/English', exist_ok=True)

    spiderC = NovelSpider()
    spiderC.crawl(pages=28211)
    # TODO 解析中文目录，代码添加注释

    spiderE = CNNSpider()
    spiderE.crawl(600)

    print("🎉 所有任务已完成！")
