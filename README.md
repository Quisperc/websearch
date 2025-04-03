# websearch
## 项目背景
    本项目起因于《互联网搜索引擎》课程，用于学习spider爬虫项目。

## 项目结构
    utils
    |--BaseSpeder.py 爬虫基类，包括爬虫的一些基础配置
    |--Fetcher.py 核心功能，包括网页查询的一些核心功能如：随机请求头生成、请求网页并保存原始网页
    |--Saver.py (弃用)原本的功能是统一化保存，不过不同爬虫需要保存的数据不同，现已经弃用，后续可能重新启用
    |--TqdmLogHandle.py Tqdm功能未使用（我未学习），另外就是日志功能
    |--WebUtils.py 网页工具，比如生成默认文件名，解码不同编码的HTML网页
    biqu_Spider.py 笔趣阁爬虫具体实现
    cnn_Spider.py （未维护）CNN网站爬虫具体实现
    kuaishu_Spider.py （未维护）快书网站爬虫具体实现
    yinyuxiaoshuo_Spider.py 英语小说网站爬虫具体实现
    crawler.py 程序入口文件，自定义配置启动

## 后言
    还有好多没做呢，加油你可以的。
![websearchTodo](https://quisper.obs.cn-east-3.myhuaweicloud.com/picgo/websearchTodo.png)