import os
from bs4 import BeautifulSoup
from utils.TqdmLogHandler import logger
from utils.dealer_en import dealer_en


def process_html_file(file_path, dealer):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, 'lxml')

        # 提取章节名称（优先从HTML内容中获取，如果失败则从文件名中提取）
        title_elem = soup.select_one('h2.text-danger.text-center.text-lg.font-bold.mt-2')
        chapter_name_from_content = title_elem.get_text(strip=True) if title_elem else None
        if not chapter_name_from_content:
            # 从文件名中提取章节名（去掉扩展名）
            chapter_name = os.path.splitext(os.path.basename(file_path))[0]
        else:
            chapter_name = chapter_name_from_content

        # 提取小说名（父目录名）
        book_name = os.path.basename(os.path.dirname(file_path))

        # 提取正文内容（根据你的选择器调整）
        content_elems = soup.select('div.c-en')
        content_text = "\n".join([elem.get_text(strip=True) for elem in content_elems])

        # 如果没有找到正文内容，则尝试从其他选择器中提取
        if not content_text:
            return

        # 清理文本并保存
        text = dealer.clean_text(content_text, uppercase=False)
        dealer._save_chapter_data(book_name, chapter_name, text)  # 使用实例方法
        logger.info(f"成功处理：{file_path}")

    except Exception as e:
        logger.error(f"处理文件 {file_path} 失败: {str(e)}")

def main():
    root_dir = r"C:\CodeProjects\PythonProject\websearch\origin\yinyu"  # 根目录
    dealer = dealer_en(dealer=None)  # 初始化处理类（确保是实例方法）

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith('.html'):
                file_path = os.path.join(dirpath, filename)
                process_html_file(file_path, dealer)


if __name__ == "__main__":
    main()