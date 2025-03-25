# TqdmLogHandler.py
from logging import Handler, Formatter, getLogger

from tqdm import tqdm


class TqdmLogHandler(Handler):
    """兼容tqdm进度条的日志处理器（避免日志打印破坏进度条显示）

    核心功能：
    - 重定向logging输出至tqdm.write方法
    - 保持进度条与日志消息的显示分离
    - 兼容所有标准logging功能

    设计背景：
    当标准logging与tqdm进度条同时使用时，日志输出会破坏进度条显示。
    本处理器通过重定向日志输出机制解决该问题。
    """

    def emit(self, record):
        """重写日志事件处理方法（关键覆盖点）

        流程：
        1. 格式化日志记录
        2. 通过tqdm.write输出
        3. 保持原始错误处理机制

        Args:
            record (LogRecord): 自动传入的日志记录对象
        """
        try:
            msg = self.format(record)  # 使用配置的formatter格式化消息
            tqdm.write(msg)  # 核心逻辑：通过tqdm的写入方法输出
        except Exception:
            self.handleError(record)  # 保持父类的错误处理逻辑


# 配置全局日志器（单例模式）
# 注意：此配置会在模块导入时立即生效
logger = getLogger("spider")  # 获取指定名称的日志器
logger.setLevel("INFO")  # 设置日志级别（过滤DEBUG信息）

# 创建并配置处理器
handler = TqdmLogHandler()  # 实例化自定义日志处理器
handler.setFormatter(Formatter("%(message)s"))  # 简化格式（仅显示原始消息）

# 禁用默认处理器防止重复输出
logger.propagate = False

# 将处理器添加到日志器
logger.addHandler(handler)  # 完成处理器注册
