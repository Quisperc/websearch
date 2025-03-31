# crawler.py
import os

from utils.TqdmLogHandler import logger
from yinyuxiaoshuo_spider import yinyuSpider

def main():

    # 配置爬虫参数
    common_config = {
        "retries": 3,
        "timeout": 30,
        "delay_range": (1, 2),
        "threads": 5
    }

    # 启动小说爬虫
    # kuaishunovel_spider = kuaishuSpider({
    #     **common_config,
    #     "delay_range": (2, 5)  # 小说站需要更保守的爬取间隔
    # })
    # delay_time = max(3, gauss(4.0, 0.6))  # 均值1秒，标准差0.3秒，最低3秒
    # delay(delay_time)
    # kuaishunovel_spider.crawl(start_page=27710, end_page=27802)

    # # 启动CNN爬虫
    # cnn_spider = CNNSpider(common_config)
    # cnn_spider.crawl(max_articles=600)

    # biqunovel_spider = biquSpider({
    #     **common_config,
    #     "delay_range": (1, 2)  # 小说站需要更保守的爬取间隔
    # })
    # biqunovel_spider.crawl(503)

    Englishnovel_spider = yinyuSpider({
        **common_config,
        "delay_range": (1, 2)  # 小说站需要更保守的爬取间隔
    })
    Englishnovel_spider.crawl(10)
    logger.info("🎉 所有任务已完成！")
    # 显示最终统计
    # logger.info("\n📊 最终统计:")
    # logger.info(f"  小说章节: {novel_spider.completed} 成功 / {novel_spider.failed} 失败")
    # logger.info(f"  CNN新闻: {cnn_spider.completed} 成功 / {cnn_spider.failed} 失败")


if __name__ == "__main__":
    main()
