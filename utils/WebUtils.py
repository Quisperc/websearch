# WebUtils.py
import re
from bs4 import BeautifulSoup

class WebUtils:
    @staticmethod
    def generate_filename(url):
        """生成安全的文件名"""
        filename = re.sub(r'://', '_', url)
        filename = re.sub(r'[^\w\.-]', '_', filename)
        filename = re.sub(r'_+', '_', filename).strip('_')
        filename = re.sub(r'\?', '_', filename).strip('_')
        return f"{filename or 'default'}.html"

    @staticmethod
    def decode_content(content, response):
        """自动检测编码并解码"""
        charset = response.headers.get_content_charset()
        if not charset:
            soup = BeautifulSoup(content, 'html.parser')
            if meta := soup.find('meta', {'charset': True}):
                charset = meta['charset']
            elif (meta := soup.find('meta', attrs={'http-equiv': re.compile(r'content-type', re.I)})) \
                    and (match := re.search(r'charset=([\w-]+)', meta.get('content', ''), re.I)):
                charset = match.group(1)

        encodings = [charset] if charset else []
        encodings += ['utf-8', 'gbk', 'latin-1', 'iso-8859-1']

        for encoding in filter(None, encodings):
            try:
                return content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue
        return content.decode('utf-8', errors='replace')
