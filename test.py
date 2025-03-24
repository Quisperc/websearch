from bs4 import BeautifulSoup  # 网页解析，获取数据
import re  # 正则表达式，进行文字匹配`
import urllib.request, urllib.error  # 制定URL，获取网页数据
import requests

# 生成文件名
def generate_filename(url):
    """生成安全的文件名，将URL中的特殊字符转换为下划线"""
    # 替换协议中的://
    filename = re.sub(r'://', '_', url)
    # 移除非字母数字、点、连字符、下划线的字符
    filename = re.sub(r'[^\w\.-]', '_', filename)
    # 合并多个连续的下划线
    filename = re.sub(r'_+', '_', filename)
    # 去除首尾的下划线并添加.txt扩展名
    filename = filename.strip('_')
    if not filename:
        filename = 'default'
    return f"{filename}.txt"

# 解码文件
def decode_content(content, response):
    """自动检测内容编码并解码"""
    # 从HTTP头获取编码
    charset = response.headers.get_content_charset()

    # 从HTML meta标签检测编码
    if not charset:
        soup = BeautifulSoup(content, 'html.parser')
        meta_charset = soup.find('meta', {'charset': True})
        if meta_charset:
            charset = meta_charset['charset']
        else:
            meta_http_equiv = soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})
            if meta_http_equiv and 'content' in meta_http_equiv.attrs:
                match = re.search(r'charset=([\w-]+)', meta_http_equiv['content'], re.I)
                if match:
                    charset = match.group(1)

    # 尝试使用检测到的编码解码
    if charset:
        try:
            return content.decode(charset)
        except (UnicodeDecodeError, LookupError):
            pass

    # 常见编码兜底
    encodings = ['utf-8', 'gbk', 'latin-1', 'iso-8859-1']
    for encoding in encodings:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    # 最终尝试用替换错误处理
    return content.decode('utf-8', errors='replace')

# 获取网页数据
def fetch_and_save(url):
    """获取并保存网页内容"""
    try:
        response = urllib.request.urlopen(url)
        content = response.read()
    except urllib.error.URLError as e:
        print(f"⚠️ 连接失败: {e.reason}")
        return
    except urllib.error.HTTPError as e:
        print(f"⛔ HTTP错误 {e.code}: {e.reason}")
        return
    except Exception as e:
        print(f"❌ 发生意外错误: {str(e)}")
        return

    # 解码内容
    decoded_content = decode_content(content, response)

    # 生成文件名并保存
    filename = generate_filename(url)
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(decoded_content)
        print(f"✅ 网页已保存为 [{filename}]")
    except IOError as e:
        print(f"🖥️ 文件写入失败: {str(e)}")


if __name__ == "__main__":
    input_url = input("🌐 请输入要爬取的URL: ")
    fetch_and_save(input_url)
