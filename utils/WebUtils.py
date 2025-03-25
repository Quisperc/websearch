# WebUtils.py
import re
from bs4 import BeautifulSoup


class WebUtils:
    """网页处理工具集

    功能模块：
    - 安全文件名生成
    - 智能编码检测与解码
    - HTML解析辅助

    典型应用场景：
    - 网页内容持久化存储
    - 处理混合编码的网页内容
    - 规范化网络资源存储路径
    """

    @staticmethod
    def generate_filename(url):
        """将URL转换为安全可用的文件名

        算法流程：
        1. 替换协议标识符（:// -> _）
        2. 过滤非法字符（保留字母数字、下划线、点、短横线）
        3. 合并连续下划线
        4. 去除首尾无效字符
        5. 保证最终文件名有效性（至少保留"default"）

        Args:
            url (str): 原始URL地址

        Returns:
            str: 规范化后的文件名，扩展名为.html

        Example:
            >>> generate_filename("https://example.com/path?query=1")
            "https_example.com_path_query=1.html"
        """
        # 协议标识符处理：将://转换为单个下划线
        filename = re.sub(r'://', '_', url)
        # 字符过滤：保留字母数字、下划线、点和短横线，其他替换为下划线
        filename = re.sub(r'[^\w\.-]', '_', filename)
        # 下划线压缩：合并连续多个下划线
        filename = re.sub(r'_+', '_', filename).strip('_')
        # 处理查询参数：替换问号为下划线
        filename = re.sub(r'\?', '_', filename).strip('_')
        # 兜底处理：空值保护，确保最小文件名
        return f"{filename or 'default'}.html"

    @staticmethod
    def decode_content(content, response):
        """智能解码网页内容（支持多级编码检测）

        解码策略（按优先级排序）：
        1. 响应头声明的charset
        2. HTML meta标签显式声明的charset
        3. 常见编码类型自动检测（utf-8 > gbk > latin-1）
        4. 强制utf-8解码（替换非法字符）

        Args:
            content (bytes): 原始二进制内容
            response (requests.Response): 响应对象

        Returns:
            str: 解码后的文本内容

        Raises:
            UnicodeDecodeError: 所有编码尝试失败时抛出（最终会强制解码）
        """
        # 第一优先级：HTTP响应头中的编码声明
        charset = response.headers.get_content_charset()

        if not charset:  # 第二优先级：HTML元数据检测
            soup = BeautifulSoup(content, 'html.parser')  # 快速解析模式

            # 检测标准meta charset标签
            if meta := soup.find('meta', {'charset': True}):
                charset = meta['charset']
            # 检测HTTP-EQUIV content-type声明
            elif (meta := soup.find('meta',
                                    attrs={'http-equiv': re.compile(r'content-type', re.I)})) \
                    and (match := re.search(r'charset=([\w-]+)',
                                            meta.get('content', ''), re.I)):
                charset = match.group(1)

        # 构建编码检测顺序列表
        encodings = [charset] if charset else []  # 前序检测结果
        encodings += ['utf-8', 'gbk', 'latin-1', 'iso-8859-1']  # 常用编码备选

        # 遍历所有候选编码
        for encoding in filter(None, encodings):  # 过滤空值
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                # LookupError处理非标准编码名称
                continue

        # 最终保障：强制UTF-8解码（替换非法字符）
        return content.decode('utf-8', errors='replace')
