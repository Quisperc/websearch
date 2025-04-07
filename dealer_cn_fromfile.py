import os
import glob
from bs4 import BeautifulSoup
from utils.dealer_cn import dealer_cn

def process_html_file(file_path, dealer):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, 'lxml')

        # 提取元数据
        meta_tag = soup.find('meta', attrs={'name': 'keywords'})
        book_name = "《诡秘之主》"
        chapter_name = "Unknown Chapter"

        if meta_tag:
            content_str = meta_tag['content']
            # 分割并提取目标部分
            # 取书名
            book_name = content_str.split(',', 1)[0].strip()
            # 处理章节名和当前页信息
            second_part = content_str.split(',', 1)[1].strip()
            second_part_split = second_part.split('.', 1)
            if len(second_part_split) > 1:
                chapter_name = second_part_split[1].strip()
            else:
                chapter_name = second_part_split[0].strip()

        # 提取正文内容（排除最后一个p标签）
        content_elems = soup.select('#chaptercontent p:not(:nth-last-of-type(-n+1))')
        content_text = "\n".join([elem.get_text(strip=True) for elem in content_elems])

        # 清理文本并保存
        text = dealer.clean_text(content_text)
        dealer._save_chapter_data(book_name, chapter_name, text)
        print(f"成功处理文件: {file_path}")

    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {str(e)}")

def main():
    folder_path = r"C:\CodeProjects\PythonProject\websearch\origin\22biqu"  # 使用原始字符串避免转义
    html_files = glob.glob(os.path.join(folder_path, "*.html"))  # 获取所有HTML文件

    dealer = dealer_cn(dealer=None)  # 初始化处理类（假设需要单例或复用）

    for file_path in html_files:
        process_html_file(file_path, dealer)

if __name__ == "__main__":
    main()