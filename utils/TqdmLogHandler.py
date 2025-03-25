# TqdmLogHandler.py
from logging import Handler, Formatter, getLogger

from tqdm import tqdm


class TqdmLogHandler(Handler):
    """将日志消息重定向到tqdm.write"""
    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.write(msg)
        except Exception:
            self.handleError(record)

# 配置全局logger
logger = getLogger("spider")
logger.setLevel("INFO")
handler = TqdmLogHandler()
handler.setFormatter(Formatter("%(message)s"))
logger.addHandler(handler)