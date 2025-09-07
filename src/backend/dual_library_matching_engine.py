#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双配方库匹配引擎
支持配方库与待匹配配方库之间的智能匹配
实现基于更新需求的两段式相似度计算算法
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

from src.backend.sql.mysql_models import (
    Formulas, FormulasToBeMatched,
    DualFormulaLibraryHandler, SystemConfigManager
)
from sqlalchemy import or_

logger = logging.getLogger(__name__)


@dataclass
class DualLibraryMatchingParameters:
    """双配方库匹配算法参数"""
    # 类别权重
    category_weights: Dict[str, float]

    # 配料组成vs配料比例权重
    composition_weight: float
    proportion_weight: float

    # 复配相似度参数
    compound_threshold: float

    # 其他参数
    min_similarity_threshold: float
    max_results: int


@dataclass
class DualLibraryMatchResult:
    """双配方库匹配结果"""
    source_formula_id: int
    source_formula_name: str
    target_formula_id: int
    target_formula_name: str
    similarity_score: float
    composition_similarity: float
    proportion_similarity: float
    category_similarities: Dict[str, float]
    common_ingredients: List[str]
    common_ingredients_count: int
    total_ingredients_count: int
    match_details: Dict


class DualLibraryMatchingEngine:
    """双配方库匹配引擎"""

    def __init__(self, parameters: DualLibraryMatchingParameters = None):
        """初始化匹配引擎"""
        self.parameters = parameters or self._get_default_parameters()

        # 成分分类缓存
        self._ingredient_categories = {}

        # 复配体系缓存
        self._compound_systems = {}

    def _get_default_parameters(self) -> DualLibraryMatchingParameters:
        """获取默认匹配参数（硬编码备用）"""
        return DualLibraryMatchingParameters(
            category_weights={
                "防腐剂": 0.35,
                "乳化剂": 0.15,
                "增稠剂": 0.15,
                "抗氧化剂": 0.1,
                "表面活性剂": 0.1,
                "其他": 0.15
            },
            composition_weight=0.8,
            proportion_weight=0.2,
            compound_threshold=0.6,
            min_similarity_threshold=0.0,
            max_results=5
        )

    def _load_parameters_from_db(self, session) -> DualLibraryMatchingParameters:
        """从数据库加载匹配参数"""
        try:
            # 获取分类权重
            category_weights = SystemConfigManager.get_category_weights(session)

            # 获取匹配算法参数
            matching_params = SystemConfigManager.get_matching_parameters(session)

            logger.info(f"从数据库加载配置成功 - 分类权重: {category_weights}")
            logger.info(f"从数据库加载配置成功 - 匹配参数: {matching_params}")

            return DualLibraryMatchingParameters(
                category_weights=category_weights,
                composition_weight=matching_params['composition_weight'],
                proportion_weight=matching_params['proportion_weight'],
                compound_threshold=matching_params['compound_threshold'],
                min_similarity_threshold=matching_params['min_similarity_threshold'],
                max_results=5  # 这个参数可以后续也加入配置
            )

        except Exception as e:
            logger.warning(f"从数据库加载配置失败，使用默认配置: {e}")
            return self._get_default_parameters()

    def match_formula_against_library(
            self,
            source_formula_id: int,
            session,
            target_formulas: List[int] = None,
            strict_mode: bool = False
    ) -> List[DualLibraryMatchResult]:
        """
        将待匹配配方与配方库进行匹配
        
        Args:
            source_formula_id: 待匹配配方ID (formulas_to_be_matched表)
            session: 数据库会话
            target_formulas: 目标配方ID列表，如果为None则匹配所有配方库配方
            
        Returns:
            匹配结果列表，按相似度降序排列
        """
        try:
            # 从数据库加载最新配置
            self.parameters = self._load_parameters_from_db(session)

            # 获取待匹配配方
            source_formula = session.query(FormulasToBeMatched).filter(
                FormulasToBeMatched.id == source_formula_id
            ).first()

            if not source_formula:
                raise ValueError(f"待匹配配方 {source_formula_id} 不存在")

            # 获取待匹配配方结构
            source_structure = DualFormulaLibraryHandler.get_formula_structure(
                source_formula_id, session, 'to_be_matched'
            )

            # 获取目标配方列表
            if target_formulas is None:
                if strict_mode:
                    # 严格范围匹配：只匹配相同产品类型和客户的配方
                    logger.info(f"严格模式匹配：产品类型={source_formula.product_type}, 客户={source_formula.customer}")

                    # 解析源配方的产品类型
                    source_product_type = source_formula.product_type or ""
                    source_customer = source_formula.customer or ""

                    # 构建查询条件
                    query = session.query(Formulas)

                    # 产品类型过滤
                    if source_product_type:
                        # 如果是新格式（大类-细分类型），精确匹配
                        # 如果是旧格式（只有大类），匹配所有相同大类的配方
                        if '-' in source_product_type:
                            # 精确匹配新格式
                            query = query.filter(Formulas.product_type == source_product_type)
                        else:
                            # 匹配相同大类的所有配方（兼容新旧格式）
                            query = query.filter(
                                or_(
                                    Formulas.product_type == source_product_type,  # 旧格式精确匹配
                                    Formulas.product_type.like(f"{source_product_type}-%")  # 新格式大类匹配
                                )
                            )

                    # 客户过滤
                    if source_customer:
                        query = query.filter(Formulas.customer == source_customer)
                    else:
                        # 如果源配方没有客户信息，只匹配同样没有客户信息的配方
                        query = query.filter(or_(Formulas.customer == "", Formulas.customer.is_(None)))

                    target_formulas_query = query.all()
                    logger.info(f"严格模式过滤后找到 {len(target_formulas_query)} 个候选配方")
                else:
                    # 常规模式：匹配所有配方
                    target_formulas_query = session.query(Formulas).all()
                    logger.info(f"常规模式匹配所有 {len(target_formulas_query)} 个配方")

                target_formula_ids = [f.id for f in target_formulas_query]
            else:
                target_formula_ids = target_formulas

            # 执行批量匹配
            match_results = []
            for target_formula_id in target_formula_ids:
                try:
                    result = self._match_single_pair(
                        source_formula, source_structure,
                        target_formula_id, session
                    )

                    if result and result.similarity_score >= self.parameters.min_similarity_threshold:
                        match_results.append(result)

                except Exception as e:
                    logger.warning(f"匹配配方 {target_formula_id} 时出错: {e}")
                    continue

            # 按相似度排序并返回前N个结果
            match_results.sort(key=lambda x: x.similarity_score, reverse=True)
            return match_results[:self.parameters.max_results]

        except Exception as e:
            logger.error(f"配方匹配失败: {e}")
            raise e

    def _match_single_pair(
            self,
            source_formula: FormulasToBeMatched,
            source_structure: Dict,
            target_formula_id: int,
            session
    ) -> Optional[DualLibraryMatchResult]:
        """匹配单个配方对"""
        try:
            # 获取目标配方
            target_formula = session.query(Formulas).filter(
                Formulas.id == target_formula_id
            ).first()

            if not target_formula:
                return None

            # 获取目标配方结构
            target_structure = DualFormulaLibraryHandler.get_formula_structure(
                target_formula_id, session, 'reference'
            )

            # 计算成分组成相似度（第一段）
            composition_similarity = self._calculate_composition_similarity(
                source_structure, target_structure, session
            )

            # 计算成分比例相似度（第二段）
            proportion_similarity = self._calculate_proportion_similarity(
                source_structure, target_structure
            )

            # 计算分类相似度
            category_similarities = self._calculate_category_similarities(
                source_structure, target_structure, session
            )

            # 计算总相似度
            total_similarity = (
                    self.parameters.composition_weight * composition_similarity +
                    self.parameters.proportion_weight * proportion_similarity
            )

            # 精度修正：避免浮点数误差
            if abs(total_similarity - 1.0) < 1e-10:
                total_similarity = 1.0
            elif abs(total_similarity) < 1e-10:
                total_similarity = 0.0

            # 获取共同成分信息
            common_ingredients = self._get_common_ingredients(
                source_structure, target_structure
            )

            # 构建匹配详情
            source_ingredients_list = self._extract_ingredients_list(source_structure)
            target_ingredients_list = self._extract_ingredients_list(target_structure)

            match_details = {
                "source_ingredients_count": len(source_ingredients_list),
                "target_ingredients_count": len(target_ingredients_list),
                "composition_method": "weighted_jaccard",
                "proportion_method": "weighted_cosine",
                "algorithm_version": "dual_library_v1.0",
                "parameters": {
                    "composition_weight": self.parameters.composition_weight,
                    "proportion_weight": self.parameters.proportion_weight,
                    "category_weights": self.parameters.category_weights
                }
            }

            # 创建匹配结果
            result = DualLibraryMatchResult(
                source_formula_id=source_formula.id,
                source_formula_name=source_formula.formula_name,
                target_formula_id=target_formula.id,
                target_formula_name=target_formula.formula_name,
                similarity_score=total_similarity,
                composition_similarity=composition_similarity,
                proportion_similarity=proportion_similarity,
                category_similarities=category_similarities,
                common_ingredients=common_ingredients,
                common_ingredients_count=len(common_ingredients),
                total_ingredients_count=len(set([ing['chinese_name'] for ing in source_ingredients_list])),
                match_details=match_details
            )

            return result

        except Exception as e:
            logger.error(f"单个配方匹配失败: {e}")
            return None

    def _calculate_composition_similarity(
            self,
            source_structure: Dict,
            target_structure: Dict,
            session
    ) -> float:
        """计算成分组成相似度（仅使用加权Jaccard）"""
        try:
            # 根据要求，组成相似度只使用加权Jaccard
            weighted_jaccard = self._calculate_weighted_jaccard_by_category(
                source_structure, target_structure, session
            )

            logger.info(f"🔍 组成相似度计算结果:")
            logger.info(f"  加权Jaccard: {weighted_jaccard:.4f}")
            logger.info(f"  最终组成相似度: {weighted_jaccard:.4f} (仅使用加权Jaccard)")

            return weighted_jaccard

        except Exception as e:
            logger.error(f"计算成分组成相似度失败: {e}")
            return 0.0

    def _calculate_proportion_similarity(
            self,
            source_structure: Dict,
            target_structure: Dict
    ) -> float:
        """计算成分比例相似度（使用并集进行加权余弦相似度计算）"""
        try:
            # 使用提取成分列表方法，保持复配整体性
            source_ingredients_list = self._extract_ingredients_list(source_structure)
            target_ingredients_list = self._extract_ingredients_list(target_structure)

            # 构建成分比例字典
            source_proportions = {}
            target_proportions = {}

            # 处理源配方比例（复配作为整体）
            for ing in source_ingredients_list:
                name = ing['chinese_name']
                content = ing.get('content', 0)
                source_proportions[name] = content

            # 处理目标配方比例（复配作为整体）
            for ing in target_ingredients_list:
                name = ing['chinese_name']
                content = ing.get('content', 0)
                target_proportions[name] = content

            # 构建并集的所有成分列表
            all_ingredients = sorted(list(set(source_proportions.keys()) | set(target_proportions.keys())))

            if len(all_ingredients) == 0:
                return 0.0

            # 构建比例向量（基于并集）
            source_vector = []
            target_vector = []

            for ingredient in all_ingredients:
                source_vector.append(source_proportions.get(ingredient, 0))
                target_vector.append(target_proportions.get(ingredient, 0))

            # 计算加权余弦相似度
            if np.sum(source_vector) == 0 or np.sum(target_vector) == 0:
                return 0.0

            source_array = np.array(source_vector).reshape(1, -1)
            target_array = np.array(target_vector).reshape(1, -1)

            cosine_sim = cosine_similarity(source_array, target_array)[0, 0]

            # 记录余弦相似度计算结果
            logger.info(f"📊 比例相似度计算结果:")
            logger.info(f"  成分并集数量: {len(all_ingredients)}")
            logger.info(f"  源配方向量: {source_vector[:5]}...({len(source_vector)} 个成分)" if len(source_vector) > 5 else f"  源配方向量: {source_vector}")
            logger.info(f"  目标配方向量: {target_vector[:5]}...({len(target_vector)} 个成分)" if len(target_vector) > 5 else f"  目标配方向量: {target_vector}")
            logger.info(f"  余弦相似度原始值: {cosine_sim:.6f}")

            # 精度修正：避免浮点数误差
            if not np.isnan(cosine_sim):
                # 如果非常接近1.0，则认为是完全相同
                if abs(cosine_sim - 1.0) < 1e-10:
                    cosine_sim = 1.0
                    logger.info(f"  余弦相似度修正为: {cosine_sim:.6f} (接近1.0)")
                # 如果非常接近0.0，则认为是完全不同
                elif abs(cosine_sim) < 1e-10:
                    cosine_sim = 0.0
                    logger.info(f"  余弦相似度修正为: {cosine_sim:.6f} (接近0.0)")
                else:
                    logger.info(f"  余弦相似度最终值: {cosine_sim:.6f}")
                return float(cosine_sim)
            else:
                logger.warning(f"  余弦相似度计算结果为NaN，返回0.0")
                return 0.0

        except Exception as e:
            logger.error(f"计算成分比例相似度失败: {e}")
            return 0.0

    def _calculate_weighted_jaccard_by_category(
            self,
            source_structure: Dict,
            target_structure: Dict,
            session
    ) -> float:
        """按分类计算加权Jaccard相似度"""
        try:
            logger.info(f"🔍 开始计算加权Jaccard相似度...")

            # 按分类分组成分 - 展开成分列表
            source_ingredients_list = self._extract_ingredients_list(source_structure)
            target_ingredients_list = self._extract_ingredients_list(target_structure)

            logger.info(f"  源配方成分总数: {len(source_ingredients_list)}")
            logger.info(f"  目标配方成分总数: {len(target_ingredients_list)}")

            source_by_category = self._group_ingredients_by_category(
                source_ingredients_list, session
            )
            target_by_category = self._group_ingredients_by_category(
                target_ingredients_list, session
            )

            logger.info(f"  源配方分类: {list(source_by_category.keys())}")
            logger.info(f"  目标配方分类: {list(target_by_category.keys())}")

            # 详细显示各分类的成分（显示数量，标识符列表在debug模式下显示）
            for category, ingredients in source_by_category.items():
                logger.info(f"    源配方-{category}: {len(ingredients)}个成分")
                logger.debug(f"      标识符列表: {ingredients}")
            for category, ingredients in target_by_category.items():
                logger.info(f"    目标配方-{category}: {len(ingredients)}个成分")
                logger.debug(f"      标识符列表: {ingredients}")

            # 计算各分类的Jaccard相似度
            category_similarities = {}
            all_categories = set(source_by_category.keys()) | set(target_by_category.keys())

            logger.info(f"  参与计算的分类: {sorted(all_categories)}")

            for category in all_categories:
                source_set = set(source_by_category.get(category, []))
                target_set = set(target_by_category.get(category, []))

                intersection = len(source_set & target_set)
                union = len(source_set | target_set)

                if union > 0:
                    category_similarities[category] = intersection / union
                else:
                    category_similarities[category] = 0.0

                logger.info(
                    f"  分类 '{category}': 交集={intersection}, 并集={union}, 相似度={category_similarities[category]:.4f}")
                if intersection > 0:
                    logger.debug(f"    共同标识符: {sorted(source_set & target_set)}")
                if len(source_set - target_set) > 0:
                    logger.debug(f"    源独有标识符: {sorted(source_set - target_set)}")
                if len(target_set - source_set) > 0:
                    logger.debug(f"    目标独有标识符: {sorted(target_set - source_set)}")

            # 加权平均 - 只对实际存在成分的分类进行计算
            logger.info(f"  开始计算加权平均...")
            weighted_similarity = 0.0
            total_weight = 0.0

            # 找出实际有成分的分类（源配方或目标配方中至少有一个有该分类）
            active_categories = set()
            for category in all_categories:
                source_set = set(source_by_category.get(category, []))
                target_set = set(target_by_category.get(category, []))
                # 只有当源配方或目标配方中至少有一个配方包含该分类时，才参与计算
                if len(source_set) > 0 or len(target_set) > 0:
                    active_categories.add(category)

            logger.info(f"  有效分类（有成分的分类）: {sorted(active_categories)}")

            # 只对有效分类进行权重计算
            for category in active_categories:
                if category in category_similarities:
                    similarity = category_similarities[category]
                    weight = self.parameters.category_weights.get(category,
                                                                  self.parameters.category_weights.get("其他", 0.15))
                    contribution = weight * similarity
                    weighted_similarity += contribution
                    total_weight += weight

                    logger.info(
                        f"    分类 '{category}': 相似度={similarity:.4f}, 权重={weight:.2f}, 贡献={contribution:.4f}")

            # 显示被跳过的空分类
            skipped_categories = set(self.parameters.category_weights.keys()) - active_categories
            if skipped_categories:
                logger.info(f"  跳过的空分类: {sorted(skipped_categories)}")

            final_weighted = weighted_similarity / total_weight if total_weight > 0 else 0.0
            logger.info(f"  参与计算的总权重: {total_weight:.2f}")
            logger.info(f"  加权总分: {weighted_similarity:.4f}")
            logger.info(f"  最终加权Jaccard: {final_weighted:.4f}")

            return final_weighted

        except Exception as e:
            logger.error(f"计算加权Jaccard相似度失败: {e}")
            return 0.0

    def _calculate_compound_similarity(self, source_compound: Dict, target_compound: Dict) -> float:
        """计算复配成分相似度（基于catalog_id的Jaccard算法）"""
        try:
            if source_compound.get('type') != 'compound' or target_compound.get('type') != 'compound':
                return 0.0

            # 获取复配中成分的catalog_id集合，确保匹配一致性
            source_catalog_ids = set()
            target_catalog_ids = set()

            # 从components_detail中提取catalog_id
            source_components = source_compound.get('components_detail', [])
            target_components = target_compound.get('components_detail', [])

            for comp in source_components:
                catalog_id = comp.get('catalog_id')
                if catalog_id:
                    source_catalog_ids.add(catalog_id)
                else:
                    logger.warning(f"复配子成分缺少catalog_id: {comp.get('chinese_name', '未知')}")

            for comp in target_components:
                catalog_id = comp.get('catalog_id')
                if catalog_id:
                    target_catalog_ids.add(catalog_id)
                else:
                    logger.warning(f"复配子成分缺少catalog_id: {comp.get('chinese_name', '未知')}")

            if not source_catalog_ids or not target_catalog_ids:
                return 0.0

            # 计算基于catalog_id的Jaccard相似度
            intersection = len(source_catalog_ids & target_catalog_ids)
            union = len(source_catalog_ids | target_catalog_ids)
            compound_similarity = intersection / union if union > 0 else 0.0

            logger.info(f"🔍 复配相似度: {compound_similarity:.4f} (交集:{intersection}, 并集:{union})")
            logger.info(f"  源复配catalog_ids: {sorted(source_catalog_ids)}")
            logger.info(f"  目标复配catalog_ids: {sorted(target_catalog_ids)}")

            return compound_similarity

        except Exception as e:
            logger.error(f"计算复配相似度失败: {e}")
            return 0.0

    def _is_compound_match_success(self, similarity: float) -> bool:
        """判断复配是否匹配成功（相似度>60%）"""
        return similarity >= self.parameters.compound_threshold

    def _calculate_category_similarities(
            self,
            source_structure: Dict,
            target_structure: Dict,
            session
    ) -> Dict[str, float]:
        """计算各分类的相似度"""
        try:
            # 展开成分列表
            source_ingredients_list = self._extract_ingredients_list(source_structure)
            target_ingredients_list = self._extract_ingredients_list(target_structure)

            source_by_category = self._group_ingredients_by_category(
                source_ingredients_list, session
            )
            target_by_category = self._group_ingredients_by_category(
                target_ingredients_list, session
            )

            similarities = {}
            all_categories = set(source_by_category.keys()) | set(target_by_category.keys())

            for category in all_categories:
                source_set = set(source_by_category.get(category, []))
                target_set = set(target_by_category.get(category, []))

                intersection = len(source_set & target_set)
                union = len(source_set | target_set)

                similarities[category] = intersection / union if union > 0 else 0.0

            return similarities

        except Exception as e:
            logger.error(f"计算分类相似度失败: {e}")
            return {}

    def _extract_ingredients_list(self, structure: Dict) -> List[Dict]:
        """从配方结构中提取成分列表 - 复配作为整体处理"""
        ingredients_list = []
        table_type = structure.get('table_type', 'reference')  # 获取表类型

        for ing in structure.get('ingredients', []):
            if ing.get('type') == 'single':
                # 单配成分 - 统一使用ingredient_content字段
                content_value = ing.get('content', 0)
                if content_value == 0:
                    # 如果content为0，尝试使用actual_content
                    content_value = ing.get('actual_content', 0)

                ingredients_list.append({
                    'type': 'single',
                    'chinese_name': ing['chinese_name'],
                    'inci_name': ing.get('inci_name', ''),
                    'content': content_value,
                    'ingredient_id': ing.get('ingredient_id'),
                    'table_type': table_type,
                    'purpose': ing.get('purpose', '其他'),  # 添加purpose字段
                    'catalog_id': ing.get('catalog_id')  # 添加catalog_id用于匹配
                })
            elif ing.get('type') == 'compound':
                # 复配成分作为整体
                components = ing.get('components', [])
                if components:
                    # 创建复配整体标识 - 基于成分组合而非ingredient_id
                    # 使用成分的中文名称排序后生成唯一标识
                    component_names = sorted([comp.get('chinese_name', '') for comp in components])
                    # 取前3个主要成分作为标识（避免名称过长）
                    main_identifiers = component_names[:3]
                    compound_identifier = '_'.join(main_identifiers)
                    # 生成简化的哈希值避免名称过长
                    import hashlib
                    compound_hash = hashlib.md5(compound_identifier.encode('utf-8')).hexdigest()[:8]
                    compound_name = f"复配_{compound_hash}"

                    # 调试信息：记录复配名称生成
                    logger.info(f"🔍 复配名称生成: {compound_name} <- 成分: {main_identifiers}")

                    # 获取复配中所有成分的catalog_id列表（用于匹配）
                    component_catalog_ids = []
                    for comp in components:
                        catalog_id = comp.get('catalog_id')
                        if catalog_id:
                            component_catalog_ids.append(catalog_id)

                    # 排序确保一致性
                    component_catalog_ids.sort()

                    ingredients_list.append({
                        'type': 'compound',
                        'chinese_name': compound_name,
                        'compound_id': ing.get('ingredient_id'),
                        'ingredient_id': ing.get('ingredient_id'),
                        'total_content': ing.get('total_content', 0),
                        'component_catalog_ids': component_catalog_ids,  # 用于匹配的catalog_id列表
                        'components_detail': components,
                        'content': ing.get('total_content', 0),
                        'table_type': table_type,
                        'purpose': ing.get('purpose', '其他')  # 添加复配整体的purpose字段
                    })
            else:
                # 兼容旧格式
                if 'chinese_name' in ing:
                    ingredients_list.append({
                        'type': 'single',
                        'chinese_name': ing['chinese_name'],
                        'inci_name': ing.get('inci_name', ''),
                        'content': ing.get('actual_content', ing.get('content', 0)),
                        'ingredient_id': ing.get('ingredient_id'),
                        'table_type': table_type
                    })

        return ingredients_list

    def _map_purpose_to_standard_category(self, purpose: str) -> str:
        """将原始purpose映射到标准分类"""
        if not purpose or not purpose.strip():
            return "其他"

        purpose = purpose.strip().lower()

        # 防腐剂关键词
        if any(keyword in purpose for keyword in ['防腐', '杀菌', '抗菌', '防霉', '抑菌', '消毒']):
            return "防腐剂"

        # 乳化剂关键词
        if any(keyword in purpose for keyword in ['乳化', '稳定', '分散', '均质']):
            return "乳化剂"

        # 增稠剂关键词
        if any(keyword in purpose for keyword in ['增稠', '稠化', '胶凝', '粘稠', '凝胶', '增粘']):
            return "增稠剂"

        # 抗氧化剂关键词
        if any(keyword in purpose for keyword in ['抗氧化', '防氧化', '还原', '清除自由基']):
            return "抗氧化剂"

        # 表面活性剂关键词
        if any(keyword in purpose for keyword in ['表面活性', '清洁', '起泡', '去污', '洗涤', '发泡', '润湿']):
            return "表面活性剂"

        # 其他常见功能也归类到"其他"
        return "其他"

    def _group_ingredients_by_category(self, ingredients: List[Dict], session) -> Dict[str, List]:
        """按分类分组成分 - 映射到标准6分类，统一使用字符串标识符"""
        try:
            grouped = defaultdict(list)

            for ingredient in ingredients:
                ingredient_type = ingredient.get('type', 'single')
                raw_purpose = ingredient.get('purpose', '')

                # 映射到标准分类
                standard_category = self._map_purpose_to_standard_category(raw_purpose)

                if ingredient_type == 'single':
                    # 单配成分：将catalog_id转换为字符串作为匹配标识符
                    catalog_id = ingredient.get('catalog_id')
                    if catalog_id:
                        # 使用前缀区分catalog_id和复配名称，保持类型一致性
                        grouped[standard_category].append(f"catalog_{catalog_id}")
                    else:
                        # 如果没有catalog_id，使用中文名作为后备
                        chinese_name = ingredient.get('chinese_name', '')
                        if chinese_name:
                            grouped[standard_category].append(f"name_{chinese_name}")
                        logger.warning(f"单配成分缺少catalog_id: {chinese_name}")
                else:
                    # 复配成分：使用复配名称作为标识符，添加前缀保持一致性
                    chinese_name = ingredient.get('chinese_name', '')
                    if chinese_name:
                        grouped[standard_category].append(f"compound_{chinese_name}")

                logger.debug(
                    f"成分映射: {ingredient.get('chinese_name', '未知')} | 原始用途: '{raw_purpose}' | 标准分类: '{standard_category}'")

            # 只返回有成分的分类，不创建空分类
            result = {k: v for k, v in grouped.items() if v}  # 过滤掉空列表

            logger.info(f"分类映射结果（成分数量）: {[(k, len(v)) for k, v in result.items()]}")
            return result

        except Exception as e:
            logger.error(f"成分分类失败: {e}")
            return {"其他": [f"catalog_{ing.get('catalog_id', '')}" if ing.get('catalog_id')
                             else f"name_{ing.get('chinese_name', '')}" for ing in ingredients]}

    def _get_common_ingredients(
            self,
            source_structure: Dict,
            target_structure: Dict
    ) -> List[str]:
        """获取共同成分"""
        # 提取成分名称集合
        source_ingredients = set()
        target_ingredients = set()

        # 处理源配方成分
        for ing in source_structure.get('ingredients', []):
            if ing.get('type') == 'single':
                source_ingredients.add(ing['chinese_name'])
            elif ing.get('type') == 'compound':
                for comp in ing.get('components', []):
                    source_ingredients.add(comp['chinese_name'])
            else:
                # 兼容旧格式
                if 'chinese_name' in ing:
                    source_ingredients.add(ing['chinese_name'])

        # 处理目标配方成分
        for ing in target_structure.get('ingredients', []):
            if ing.get('type') == 'single':
                target_ingredients.add(ing['chinese_name'])
            elif ing.get('type') == 'compound':
                for comp in ing.get('components', []):
                    target_ingredients.add(comp['chinese_name'])
            else:
                # 兼容旧格式
                if 'chinese_name' in ing:
                    target_ingredients.add(ing['chinese_name'])

        return sorted(list(source_ingredients & target_ingredients))

    def batch_match_formulas(
            self,
            source_formula_ids: List[int],
            session,
            target_formulas: List[int] = None
    ) -> Dict[int, List[DualLibraryMatchResult]]:
        """批量匹配多个配方"""
        results = {}

        for source_id in source_formula_ids:
            try:
                match_results = self.match_formula_against_library(
                    source_id, session, target_formulas
                )
                results[source_id] = match_results
            except Exception as e:
                logger.error(f"批量匹配配方 {source_id} 失败: {e}")
                results[source_id] = []

        return results

    def get_matching_statistics(self, match_results: List[DualLibraryMatchResult]) -> Dict:
        """获取匹配统计信息"""
        if not match_results:
            return {}

        similarities = [r.similarity_score for r in match_results]

        return {
            "total_matches": len(match_results),
            "avg_similarity": np.mean(similarities),
            "max_similarity": np.max(similarities),
            "min_similarity": np.min(similarities),
            "std_similarity": np.std(similarities),
            "high_similarity_count": len([s for s in similarities if s >= 0.8]),
            "medium_similarity_count": len([s for s in similarities if 0.5 <= s < 0.8]),
            "low_similarity_count": len([s for s in similarities if s < 0.5])
        }


if __name__ == "__main__":
    print("🔍 双配方库匹配引擎")
    print("支持配方库与待匹配配方库之间的智能匹配")
    print("实现两段式相似度计算：成分组成 + 成分比例")
