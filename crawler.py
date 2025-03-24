# crawler.py
from utils import Fetcher, Saver
from CNNSpider import CNNSpider


if __name__ == "__main__":
    import os

    # 创建存储目录
    os.makedirs('origin', exist_ok=True)
    os.makedirs('parsed', exist_ok=True)

    # spiderC = webSpider()
    # spiderC.crawl(pages=27810)

    spiderE = CNNSpider()
    spiderE.crawl(2)

    print("🎉 所有任务已完成！")
