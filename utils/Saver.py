# Saver.py
import csv
from pathlib import Path

import pandas as pd

from utils.TqdmLogHandler import logger


class Saver:
    @staticmethod
    def save_data(data, save_dir="parsed", exclude_columns=None, format_type='both'):
        """通用数据保存方法"""
        try:
            base_dir = Path(save_dir)
            base_dir.mkdir(parents=True, exist_ok=True)

            # 保存结构化数据
            if format_type in ('csv', 'both') and data:
                csv_path = base_dir / "results.csv"
                Saver._save_csv(data, csv_path, exclude_columns)

            if format_type in ('excel', 'both') and data:
                excel_path = base_dir / "results.xlsx"
                Saver._save_excel(data, excel_path, exclude_columns)

            # 保存文本文件
            Saver._save_txt_files(data, base_dir)

        except PermissionError:
            logger.info("❌ 权限错误：请关闭已打开的结果文件")
        except Exception as e:
            logger.info(f"❌ 保存失败: {str(e)}")

    @staticmethod
    def _save_csv(data, path, exclude_columns):
        # 收集所有可能的字段（排除指定列）
        all_fields = set()
        for item in data:
            all_fields.update(item.keys())
        fieldnames = [f for f in all_fields if f not in (exclude_columns or [])]
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)

    @staticmethod
    def _save_excel(data, path, exclude_columns):
        df = pd.DataFrame(data)
        df.drop(columns=exclude_columns or [], inplace=True, errors='ignore')
        df.to_excel(path, index=False)

    @staticmethod
    def _save_txt_files(data, base_dir):
        txt_dir = base_dir / "articles"
        txt_dir.mkdir(exist_ok=True)

        for item in data:
            if not item.get('title'):
                continue

            filename = f"{item['title'][:50].replace(' ', '_')}.txt"
            try:
                with (txt_dir / filename).open('w', encoding='utf-8') as f:
                    f.write(f"Title: {item.get('title', '')}\n")
                    f.write(f"Url: {item.get('url', '')}\n")
                    f.write(f"Author: {item.get('author', '')}\n")
                    f.write(f"Date: {item.get('publish_time', '')}\n\n")
                    f.write(item.get('content', ''))
            except Exception as e:
                logger.info(f"⚠️ 保存文件 {filename} 失败: {str(e)}")