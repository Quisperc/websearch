import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
import jieba
from utils.TqdmLogHandler import logger

class dealer_cn:
    stopwords = set()  # 类变量，存储停用词
    def __init__(self, dealer = None):
        self.dealer = dealer
        # 初始化时加载停用词
        self.load_stopwords()

    @staticmethod
    def load_stopwords(filename='sources/cn_stopwords.txt'):
        """加载停用词表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for word in f:
                    dealer_cn.stopwords.add(word.strip())
            logger.info(f"成功加载停用词表，共{len(dealer_cn.stopwords)}个停用词")
        except FileNotFoundError:
            logger.error(f"停用词文件 {filename} 未找到！")
            dealer_cn.stopwords = set()  # 防止后续报错

    @staticmethod
    def add_stopword(word):
        """添加单个停用词"""
        dealer_cn.stopwords.add(word.strip())

    @staticmethod
    def delete_stop_words(words):
        """过滤停用词"""
        return [word for word in words if word not in dealer_cn.stopwords]

    @staticmethod
    def reload_stopwords(filename='sources/cn_stopwords.txt'):
        """重新加载停用词表"""
        dealer_cn.stopwords.clear()
        dealer_cn.load_stopwords(filename)

    @staticmethod
    def clean_text(content):
        # 清理HTML标签（如果文本来自网页）
        # soup = BeautifulSoup(content, 'html.parser')
        # text = soup.get_text()
        text = content

        # 删除特殊字符（保留字母、数字和空格）
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\n', '', text)

        # 分词
        words = dealer_cn.text_cut(text)

        # 过滤停用词
        words = dealer_cn.delete_stop_words(words)

        # 处理大小写（如果需要）
        # words = [word.lower() for word in words]  # 转换为小写
        # words = [word.upper() for word in words]  # 转换为大写
        # 便于保存：
        logger.info(f"分词结果：{' '.join(words)}")
        # logger.info(f"处理后的文本：{words}")

        # 转成文本
        text = ' '.join(words)
        return text

    @staticmethod
    def text_cut(text):
        """使用jieba进行中文分词"""
        seg_list = list(jieba.cut(text, HMM=True))  # 转换为列表方便后续处理
        return seg_list

    def _save_chapter_data(self, book_name: str, chapter_name: str,
                           content: str) -> None:
        """统一的章节保存方法"""
        try:
            # 生成安全文件名
            safe_book_name = re.sub(r'[\\/*?:"<>|]', '', book_name)[:50]
            safe_chapter_name = re.sub(r'[\\/*?:"<>|]', '', chapter_name)[:50]

            # 创建存储路径
            save_dir = Path("dealer") / safe_book_name
            save_dir.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            file_path = save_dir / f"{safe_book_name}-{safe_chapter_name}.txt"
            with file_path.open("w", encoding="utf-8-sig") as f:
                f.write(content)

            logger.info(f"✅ 成功保存处理后的中文文档: {file_path}")
        except Exception as e:
            logger.error(f"🛑 文件保存失败: {str(e)}", exc_info=True)