# crawler.py
from random import random, gauss
from turtle import delay

from cnn_spider import CNNSpider
from kuaishu_spider import kuaishuSpider

from biqu_Spider import biquSpider
from utils.TqdmLogHandler import logger
from yinyuxiaoshuo_spider import yinyuSpider


def main():
    # 初始化目录结构
    # Path("origin/Chin").mkdir(parents=True, exist_ok=True)
    # Path("origin/Engl").mkdir(parents=True, exist_ok=True)
    # Path("parsed/cnn").mkdir(parents=True, exist_ok=True)
    # Path("parsed/novel").mkdir(parents=True, exist_ok=True)

    # 配置爬虫参数
    common_config = {
        "retries": 3,
        "timeout": 15,
        "delay_range": (1, 3),
        "threads": 5
    }

    # 启动小说爬虫
    # novel_spider = NovelSpider({
    #     **common_config,
    #     "delay_range": (2, 5)  # 小说站需要更保守的爬取间隔
    # })
    # novel_spider.crawl(start_page=27710, end_page=27749)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=27750, end_page=27802)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=28166, end_page=28220)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=27960, end_page=28103)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=27803, end_page=27834)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=27934, end_page=27989)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=27835, end_page=27933)
    #
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # novel_spider.crawl(start_page=28098, end_page=28174)


    # # 启动CNN爬虫
    # cnn_spider = CNNSpider(common_config)
    # cnn_spider.crawl(max_articles=600)

    # novel_spider = biquSpider({
    #     **common_config,
    #     "delay_range": (2, 5)  # 小说站需要更保守的爬取间隔
    # })
    # novel_spider.crawl(503)

    novel_spider = yinyuSpider({
        **common_config,
        "delay_range": (2, 5)  # 小说站需要更保守的爬取间隔
    })
    novel_spider.crawl(1)
    logger.info("🎉 所有任务已完成！")
    # 显示最终统计
    # logger.info("\n📊 最终统计:")
    # logger.info(f"  小说章节: {novel_spider.completed} 成功 / {novel_spider.failed} 失败")
    # logger.info(f"  CNN新闻: {cnn_spider.completed} 成功 / {cnn_spider.failed} 失败")


if __name__ == "__main__":
    main()
