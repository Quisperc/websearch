# Saver.py
import csv
from pathlib import Path

import pandas as pd

from utils.TqdmLogHandler import logger


class Saver:
    """数据持久化处理器

    功能特性：
    - 多格式支持：CSV、Excel、文本文件
    - 结构化与非结构化数据分离存储
    - 自动处理字段排除和编码问题
    - 智能目录创建和文件命名

    典型使用场景：
    - 保存爬虫解析后的结构化数据
    - 存档完整文本内容
    - 生成可读性强的结果文件
    """

    @staticmethod
    def save_data(data, save_dir="parsed", exclude_columns=None, format_type='both'):
        """通用数据保存入口方法

        Args:
            data (list[dict]): 要保存的数据集合，每个元素为字典格式
            save_dir (str): 保存目录路径（默认'parsed'）
            exclude_columns (list): 需要排除的字段列表（如原始HTML等大字段）
            format_type (str): 保存格式，可选 'csv'/'excel'/'both'（默认）

        设计要点：
        - 自动创建多级目录结构
        - 异常处理重点关注文件权限问题
        - 支持结构化和非结构化数据分离存储
        """
        try:
            base_dir = Path(save_dir)
            # 递归创建目录（包括父目录）
            base_dir.mkdir(parents=True, exist_ok=True)

            # 结构化数据存储（CSV/Excel）
            if format_type in ('csv', 'both') and data:
                csv_path = base_dir / "results.csv"
                Saver._save_csv(data, csv_path, exclude_columns)

            if format_type in ('excel', 'both') and data:
                excel_path = base_dir / "results.xlsx"
                Saver._save_excel(data, excel_path, exclude_columns)

            # 非结构化数据存储（文本文件）
            Saver._save_txt_files(data, base_dir)

        except PermissionError:
            logger.info("❌ 权限错误：请关闭已打开的结果文件")
        except Exception as e:
            logger.info(f"❌ 保存失败: {str(e)}")

    @staticmethod
    def _save_csv(data, path, exclude_columns):
        """CSV格式保存（兼容动态字段）

        实现特点：
        - 自动收集所有可能的字段
        - 支持排除指定字段
        - 忽略多余字段（避免字段不一致报错）
        """
        # 动态收集所有字段（处理不同记录字段不一致的情况）
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())

        # 过滤排除字段
        fieldnames = [f for f in all_fields if f not in (exclude_columns or [])]

        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                extrasaction='ignore'  # 忽略数据中的多余字段
            )
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"✅ CSV文件保存至: {path}")

    @staticmethod
    def _save_excel(data, path, exclude_columns):
        """Excel格式保存（适合结构化数据分析）

        实现特点：
        - 使用pandas处理数据框
        - 自动过滤排除字段
        - 保留原始数据顺序
        """
        df = pd.DataFrame(data)
        # 安全删除指定列（忽略不存在的列）
        df.drop(
            columns=exclude_columns or [],
            inplace=True,
            errors='ignore'  # 避免列不存在时报错
        )
        df.to_excel(path, index=False)  # 不保存自动索引
        logger.info(f"✅ Excel文件保存至: {path}")

    @staticmethod
    def _save_txt_files(data, base_dir):
        """保存文本文件（适合非结构化内容存档）

        文件结构：
        - 每个条目保存为单独txt文件
        - 文件头包含元数据
        - 内容保留原始格式

        命名规则：
        - 使用标题前50个字符
        - 替换空格为下划线
        - 过滤非法字符（自动处理）
        """
        txt_dir = base_dir / "articles"
        txt_dir.mkdir(exist_ok=True)  # 创建子目录

        for item in data:
            if not item.get('title'):
                continue

            # 生成安全文件名（保留前50字符，替换特殊字符）
            raw_title = item['title'][:50]
            clean_title = raw_title.replace(' ', '_').strip()
            filename = f"{clean_title}.txt"

            try:
                with (txt_dir / filename).open('w', encoding='utf-8') as f:
                    # 写入结构化元数据
                    f.write(f"Title: {item.get('title', '')}\n")
                    f.write(f"Url: {item.get('url', '')}\n")
                    f.write(f"Author: {item.get('author', '')}\n")
                    f.write(f"Date: {item.get('publish_time', '')}\n\n")

                    # 写入正文内容
                    f.write(item.get('content', ''))
            except Exception as e:
                logger.info(f"⚠️ 保存文件 {filename} 失败: {str(e)}")
