#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配方表解析器
负责解析Excel配方表文件并提取成分信息
"""

import pandas as pd
import numpy as np
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FormulaParser:
    """配方表解析器"""

    def __init__(self):
        """初始化解析器"""
        # 支持的文件格式
        self.supported_formats = ['.xlsx', '.xls']

        # 表头关键词
        self.header_keywords = [
            '序号', '标准中文名称', '中文名称', 'inci名称', '英文名称',
            '原料含量', '含量', '%', '使用目的', '目的', '备注'
        ]

        # 列名映射规则
        self.column_mapping_rules = {
            'sequence': ['序号', 'NO', 'No', 'no', '编号'],
            'chinese_name': ['标准中文名称', '中文名称', '原料名称', '成分名称', '名称'],
            'inci_name': ['INCI名称', 'inci名称', '英文名称', 'INCI', 'inci'],
            'percentage': ['原料含量', '含量', '百分比', '%', '原料含量(%)', '含量(%)'],
            'ingredient_percentage': ['原料中成份含量', '成分含量', '原料中成分含量', '成份含量'],
            'actual_percentage': ['实际成份含量', '实际含量', '实际成分含量'],
            'purpose': ['使用目的', '目的', '功能', '用途'],
            'notes': ['备注', '说明', '注释', 'remark']
        }

    def parse_file(self, file_path: str) -> Dict:
        """
        解析配方表文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析结果字典
        """
        try:
            logger.info(f"开始解析配方表文件: {file_path}")

            # 验证文件
            if not self._validate_file(file_path):
                raise ValueError(f"不支持的文件格式或文件不存在: {file_path}")

            # 读取Excel文件
            raw_data = self._read_excel_file(file_path)

            # 查找表头行
            header_row = self._find_header_row(raw_data)
            if header_row is None:
                raise ValueError("无法找到有效的表头行")

            # 重新读取数据并设置表头
            df = pd.read_excel(file_path, header=header_row)

            # 提取配方名称
            formula_name = self._extract_formula_name(raw_data, file_path)

            # 解析成分数据
            ingredients = self._parse_ingredients(df)

            # 数据验证
            validation_result = self._validate_ingredients(ingredients)

            result = {
                'name': formula_name,
                'file_path': file_path,
                'ingredients': ingredients,
                'validation': validation_result,
                'total_ingredients': len(ingredients),
                'header_row': header_row
            }

            logger.info(f"配方表解析成功: {formula_name}, 共{len(ingredients)}个成分")
            return result

        except Exception as e:
            logger.error(f"配方表解析失败: {e}")
            raise

    def parse_multiple_files(self, file_paths: List[str]) -> List[Dict]:
        """
        批量解析多个配方表文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            解析结果列表
        """
        results = []
        failed_files = []

        for file_path in file_paths:
            try:
                result = self.parse_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"文件解析失败 {file_path}: {e}")
                failed_files.append({'file_path': file_path, 'error': str(e)})

        logger.info(f"批量解析完成: 成功{len(results)}个, 失败{len(failed_files)}个")

        return {
            'successful': results,
            'failed': failed_files,
            'total_files': len(file_paths),
            'success_count': len(results),
            'failure_count': len(failed_files)
        }

    def _validate_file(self, file_path: str) -> bool:
        """验证文件是否有效"""
        if not os.path.exists(file_path):
            return False

        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.supported_formats

    def _read_excel_file(self, file_path: str) -> pd.DataFrame:
        """读取Excel文件"""
        try:
            # 尝试读取第一个工作表
            return pd.read_excel(file_path, header=None, sheet_name=0)
        except Exception as e:
            logger.error(f"读取Excel文件失败: {e}")
            raise

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """查找表头行"""
        for i in range(min(10, len(df))):  # 只在前10行查找
            row_text = ""
            for j in range(min(8, len(df.columns))):
                cell = df.iloc[i, j]
                if pd.notna(cell):
                    row_text += str(cell).lower() + " "

            # 检查是否包含表头关键词
            keyword_count = sum(1 for keyword in self.header_keywords
                                if keyword.lower() in row_text)

            if keyword_count >= 3:  # 至少包含3个关键词
                return i

        return None

    def _extract_formula_name(self, raw_data: pd.DataFrame, file_path: str) -> str:
        """提取配方名称"""
        # 尝试从前几行中提取配方名称
        for i in range(min(5, len(raw_data))):
            for j in range(min(3, len(raw_data.columns))):
                cell = raw_data.iloc[i, j]
                if pd.notna(cell):
                    cell_str = str(cell).strip()
                    # 如果包含"配方"、"产品"等关键词，且长度合适
                    if any(keyword in cell_str for keyword in ['配方', '产品', '化妆品']) and 5 <= len(cell_str) <= 50:
                        return cell_str

        # 如果没找到，使用文件名
        return Path(file_path).stem

    def _parse_ingredients(self, df: pd.DataFrame) -> List[Dict]:
        """解析成分数据"""
        ingredients = []

        # 处理合并单元格的NaN值 - 向前填充
        df_processed = self._handle_merged_cells(df)

        # 映射列名
        column_mapping = self._map_columns(df_processed.columns)

        for idx, row in df_processed.iterrows():
            try:
                # 检查第一列是否为序号
                seq_val = row.iloc[0]
                if pd.notna(seq_val):
                    seq_str = str(seq_val).strip()
                    # 检查是否为数字（整数或浮点数）
                    if self._is_number(seq_str):
                        sequence = int(float(seq_str))

                        # 提取其他字段
                        chinese_name = self._safe_extract_text(row, column_mapping.get('chinese_name', 1))
                        inci_name = self._safe_extract_text(row, column_mapping.get('inci_name', 2))
                        percentage = self._extract_percentage(row, column_mapping.get('percentage', 3))
                        ingredient_percentage = self._extract_percentage(row,
                                                                         column_mapping.get('ingredient_percentage', 4))
                        actual_percentage = self._extract_percentage(row, column_mapping.get('actual_percentage', 5))
                        purpose = self._safe_extract_text(row, column_mapping.get('purpose', 6))
                        notes = self._safe_extract_text(row, column_mapping.get('notes', 7))

                        # 只添加有中文名称的成分
                        if chinese_name and chinese_name.lower() not in ['nan', '', '无']:
                            ingredient = {
                                'sequence': sequence,
                                'chinese_name': chinese_name,
                                'inci_name': inci_name,
                                'percentage': percentage,
                                'ingredient_percentage': ingredient_percentage,
                                'actual_percentage': actual_percentage,
                                'purpose': purpose,
                                'notes': notes,
                                'is_compound': self._detect_compound(chinese_name, inci_name, purpose)
                            }
                            ingredients.append(ingredient)

            except Exception as e:
                logger.warning(f"解析第{idx}行时出错: {e}")
                continue

        return ingredients

    def _map_columns(self, columns: List[str]) -> Dict[str, int]:
        """映射列名到索引"""
        mapping = {}

        for i, col in enumerate(columns):
            col_str = str(col).lower().strip()

            # 检查每个字段类型
            for field_type, keywords in self.column_mapping_rules.items():
                for keyword in keywords:
                    if keyword.lower() in col_str:
                        if field_type not in mapping:  # 避免重复映射
                            mapping[field_type] = i
                        break

        return mapping

    def _handle_merged_cells(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理合并单元格的NaN值"""
        df_copy = df.copy()

        # 对每一列进行处理
        for col in df_copy.columns:
            # 向前填充NaN值（合并单元格的典型模式）
            df_copy[col] = df_copy[col].ffill()

        # 特别处理序号列的合并单元格
        first_col = df_copy.iloc[:, 0]
        for i in range(1, len(first_col)):
            # 如果当前行的序号为NaN，但有中文名称，尝试找到对应的序号
            if pd.isna(first_col.iloc[i]) or str(first_col.iloc[i]).strip() == '':
                # 检查是否有中文名称（第二列通常是中文名称）
                if len(df_copy.columns) > 1:
                    chinese_name = df_copy.iloc[i, 1]
                    if pd.notna(chinese_name) and str(chinese_name).strip():
                        # 向前查找最近的序号
                        for j in range(i - 1, -1, -1):
                            prev_seq = first_col.iloc[j]
                            if pd.notna(prev_seq) and self._is_number(str(prev_seq)):
                                # 这是复配成分，使用相同的序号
                                df_copy.iloc[i, 0] = prev_seq
                                break

        return df_copy

    def _safe_extract_text(self, row, col_idx: int) -> str:
        """安全提取文本值"""
        if col_idx is None or col_idx >= len(row):
            return ""

        value = row.iloc[col_idx]
        if pd.notna(value):
            return str(value).strip()
        return ""

    def _extract_percentage(self, row, col_idx: int) -> float:
        """提取百分比值"""
        if col_idx is None or col_idx >= len(row):
            return 0.0

        value = row.iloc[col_idx]
        if pd.notna(value):
            try:
                # 移除百分号并转换为浮点数
                val_str = str(value).replace('%', '').strip()
                return float(val_str)
            except (ValueError, TypeError):
                return 0.0
        return 0.0

    def _is_number(self, s: str) -> bool:
        """检查字符串是否为数字"""
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _detect_compound(self, chinese_name: str, inci_name: str, purpose: str) -> bool:
        """检测是否为复配成分"""
        text = f"{chinese_name} {inci_name} {purpose}".lower()

        # 复配关键词
        compound_keywords = [
            '复配', '混合', '组合', '复合', '体系', '配方',
            '多元', '综合', '复方', '混配'
        ]

        return any(keyword in text for keyword in compound_keywords)

    def _validate_ingredients(self, ingredients: List[Dict]) -> Dict:
        """验证配方数据"""
        validation = {
            'total_ingredients': len(ingredients),
            'total_percentage': 0.0,
            'missing_chinese_names': 0,
            'missing_percentages': 0,
            'missing_inci_names': 0,
            'percentage_range_errors': 0,
            'compound_count': 0,
            'warnings': [],
            'errors': [],
            'is_valid': True
        }

        for ingredient in ingredients:
            # 统计缺失数据
            if not ingredient.get('chinese_name'):
                validation['missing_chinese_names'] += 1
                validation['errors'].append(f"序号{ingredient.get('sequence', '?')}缺少中文名称")

            if not ingredient.get('inci_name'):
                validation['missing_inci_names'] += 1
                validation['warnings'].append(f"{ingredient.get('chinese_name', '未知')}缺少INCI名称")

            # 检查百分比
            percentage = ingredient.get('percentage', 0)
            if percentage <= 0:
                validation['missing_percentages'] += 1
                validation['warnings'].append(f"{ingredient.get('chinese_name', '未知')}缺少含量信息")
            elif percentage > 100:
                validation['percentage_range_errors'] += 1
                validation['errors'].append(f"{ingredient.get('chinese_name', '未知')}含量超过100%")
            else:
                validation['total_percentage'] += percentage

            # 统计复配成分
            if ingredient.get('is_compound', False):
                validation['compound_count'] += 1

        # 检查总百分比
        deviation = abs(validation['total_percentage'] - 100.0)
        if deviation > 2.0:  # 允许2%的误差
            validation['warnings'].append(f"总含量为{validation['total_percentage']:.2f}%，偏离100%")
            if deviation > 5.0:  # 超过5%认为是错误
                validation['errors'].append(f"总含量严重偏离100%: {validation['total_percentage']:.2f}%")
                validation['is_valid'] = False

        # 如果有严重错误，标记为无效
        if validation['errors']:
            validation['is_valid'] = False

        return validation
