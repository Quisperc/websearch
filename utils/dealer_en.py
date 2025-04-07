import re
from pathlib import Path
from utils.TqdmLogHandler import logger
from nltk.stem import PorterStemmer

class dealer_en:
    """英文文本处理类"""
    stopwords = set()  # 停用词集合

    def __init__(self, dealer=None):
        self.dealer = dealer
        # 初始化时加载停用词
        self.load_stopwords()

    @staticmethod
    def load_stopwords(filename='sources/en_stopwords.txt'):
        """加载停用词表"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for word in f:
                    dealer_en.stopwords.add(word.strip())
            logger.info(f"成功加载停用词表，共{len(dealer_en.stopwords)}个停用词")
        except FileNotFoundError:
            logger.error(f"停用词文件 {filename} 未找到！")
            dealer_en.stopwords = set()  # 防止后续报错

    @staticmethod
    def delete_stop_words(words):
        """过滤停用词"""
        return [word for word in words if word not in dealer_en.stopwords]

    def text_cut(self, text):
        """分词函数"""
        # 这里可以使用更复杂的分词算法，比如NLTK、spaCy等
        # 这里简单地按空格分词
        return text.split()

    def stem_words(self, words):
        """词干提取函数"""
        stemmer = PorterStemmer()
        return [stemmer.stem(word) for word in words]

    def clean_text(self, text, uppercase=False):
        """清理文本"""
        # 删除特殊字符（保留字母、数字和空格）
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\n', '', text)

        # 分词
        words = self.text_cut(text)

        # 保留原始大小写
        origin_words = [word for word in words if word.isalpha()]  # 保留字母

        # 转换为小写
        words = [word.lower() for word in words]

        # 过滤停用词
        words = self.delete_stop_words(words)

        # 词干提取
        words = self.stem_words(words)

        # 处理大小写（如果需要）
        if uppercase:
        # words = [word.lower() for word in words]  # 转换为小写
            words = [word.upper() for word in words]  # 转换为大写

        text = ' '.join(words)
        return text

    def _save_chapter_data(self, book_name: str, chapter_name: str,
                           text: str) -> None:
        """统一的章节保存方法"""
        try:
            # 生成安全文件名
            safe_book_name = re.sub(r'[\\/*?:"<>|]', '_', book_name).strip()
            safe_chapter_name = re.sub(r'[\\/*?:"<>|]', '_', chapter_name).strip()

            # 创建存储路径
            save_dir = Path("dealer") / safe_book_name
            save_dir.mkdir(parents=True, exist_ok=True)

            # 写入文件内容
            file_path = save_dir / f"{safe_book_name}-{safe_chapter_name}.txt"
            with file_path.open("w", encoding="utf-8-sig") as f:
                f.write(text)

            logger.info(f"✅ 成功保存预处理的文档: {file_path}")
        except Exception as e:
            logger.error(f"🛑 文件保存失败: {str(e)}", exc_info=True)