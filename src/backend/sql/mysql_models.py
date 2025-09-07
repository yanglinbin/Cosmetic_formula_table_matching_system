#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新的数据库模型
支持双配方库架构：配方库(被匹配) + 待匹配配方库
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, Text, \
    DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Dict, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()


class Users(Base):
    """用户表"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    username = Column(String(16), nullable=False, unique=True, comment='用户名(1-16位英文数字符号)')
    password = Column(String(255), nullable=False, comment='密码(4-16位)')
    role = Column(String(20), nullable=False, default='user', comment='用户角色: user/admin')
    is_active = Column(Boolean, default=True, comment='是否激活')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    last_login = Column(DateTime, comment='最后登录时间')

    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_role', 'role'),
    )


class IngredientCatalog(Base):
    """化妆品原料目录表"""
    __tablename__ = 'ingredient_catalog'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    chinese_name = Column(String(200), nullable=False, comment='中文名称')
    inci_name = Column(String(500), comment='INCI名称/英文名称')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    __table_args__ = (
        Index('idx_chinese_name', 'chinese_name'),
        Index('idx_inci_name', 'inci_name'),
    )


# ==================== 配方库表组 (被匹配的参考配方) ====================

class Formulas(Base):
    """配方库主表 - 被匹配的参考配方"""
    __tablename__ = 'formulas'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    formula_name = Column(String(500), nullable=False, comment='配方表名称')
    product_type = Column(String(100), comment='产品类型')
    customer = Column(String(200), comment='客户')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='上传用户ID')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')

    # 关系
    ingredients = relationship("FormulaIngredients", back_populates="formula", cascade="all, delete-orphan")
    user = relationship("Users", backref="formulas")

    __table_args__ = (
        Index('idx_formula_name', 'formula_name'),
        Index('idx_product_type', 'product_type'),
        Index('idx_customer', 'customer'),
        Index('idx_user_id', 'user_id'),
    )


class FormulaIngredients(Base):
    """配方库成分表 - 被匹配的参考配方成分"""
    __tablename__ = 'formula_ingredients'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    formula_id = Column(Integer, ForeignKey('formulas.id'), nullable=False, comment='配方表id')
    ingredient_id = Column(Integer, nullable=False, comment='配料id')
    ingredient_content = Column(DECIMAL(12, 8), comment='原料含量(高精度)')
    ingredient_sequence = Column(Integer, comment='配料序号')
    standard_chinese_name = Column(String(200), nullable=False, comment='标准中文名称')
    inci_name = Column(String(500), comment='inci名称')
    catalog_id = Column(Integer, ForeignKey('ingredient_catalog.id'), comment='关联原料目录id')
    component_content = Column(DECIMAL(12, 8), comment='原料中成分含量(高精度)')
    actual_component_content = Column(DECIMAL(12, 8), comment='实际成分含量(高精度)')
    purpose = Column(String(100), comment='使用目的/配料分类')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')

    # 关系
    formula = relationship("Formulas", back_populates="ingredients")
    catalog = relationship("IngredientCatalog", backref="formula_ingredients")

    __table_args__ = (
        Index('idx_formula_ingredient', 'formula_id', 'ingredient_id'),
        Index('idx_formula_sequence', 'formula_id', 'ingredient_id', 'ingredient_sequence'),
        Index('idx_catalog_id', 'catalog_id'),
        Index('idx_standard_chinese_name', 'standard_chinese_name'),
    )


# ==================== 待匹配配方表组 (用户上传的配方) ====================

class FormulasToBeMatched(Base):
    """待匹配配方主表 - 用户上传的配方"""
    __tablename__ = 'formulas_to_be_matched'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    formula_name = Column(String(500), nullable=False, comment='配方表名称')
    product_type = Column(String(100), comment='产品类型')
    customer = Column(String(200), comment='客户')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='上传用户ID')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')

    # 关系
    ingredients = relationship("FormulaIngredientsToBeMatched", back_populates="formula", cascade="all, delete-orphan")
    user = relationship("Users", backref="to_be_matched_formulas")

    __table_args__ = (
        Index('idx_to_be_matched_formula_name', 'formula_name'),
        Index('idx_to_be_matched_product_type', 'product_type'),
        Index('idx_to_be_matched_customer', 'customer'),
        Index('idx_to_be_matched_user_id', 'user_id'),
    )


class FormulaIngredientsToBeMatched(Base):
    """待匹配配方成分表 - 用户上传的配方成分"""
    __tablename__ = 'formula_ingredients_to_be_matched'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键')
    formula_id = Column(Integer, ForeignKey('formulas_to_be_matched.id'), nullable=False, comment='配方表id')
    ingredient_id = Column(Integer, nullable=False, comment='配料id')
    ingredient_content = Column(DECIMAL(12, 8), comment='原料含量(高精度)')
    ingredient_sequence = Column(Integer, comment='配料序号')
    standard_chinese_name = Column(String(200), nullable=False, comment='标准中文名称')
    inci_name = Column(String(500), comment='inci名称')
    catalog_id = Column(Integer, ForeignKey('ingredient_catalog.id'), comment='关联原料目录id')
    component_content = Column(DECIMAL(12, 8), comment='原料中成分含量(高精度)')
    actual_component_content = Column(DECIMAL(12, 8), comment='实际成分含量(高精度)')
    purpose = Column(String(100), comment='使用目的/配料分类')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='修改时间')

    # 关系
    formula = relationship("FormulasToBeMatched", back_populates="ingredients")
    catalog = relationship("IngredientCatalog", backref="formula_ingredients_to_be_matched")

    __table_args__ = (
        Index('idx_to_be_matched_formula_ingredient', 'formula_id', 'ingredient_id'),
        Index('idx_to_be_matched_formula_sequence', 'formula_id', 'ingredient_id', 'ingredient_sequence'),
        Index('idx_to_be_matched_catalog_id', 'catalog_id'),
        Index('idx_to_be_matched_standard_chinese_name', 'standard_chinese_name'),
    )


# ==================== 匹配功能表组 ====================

class FormulaMatchRecord(Base):
    """配方匹配记录表"""
    __tablename__ = 'formula_match_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_formula_id = Column(Integer, ForeignKey('formulas_to_be_matched.id'), comment='源配方ID(待匹配)')
    target_formula_id = Column(Integer, ForeignKey('formulas.id'), comment='目标配方ID(配方库)')
    similarity_score = Column(DECIMAL(8, 6), comment='总相似度得分(高精度)')
    composition_similarity = Column(DECIMAL(8, 6), comment='成分组成相似度(高精度)')
    proportion_similarity = Column(DECIMAL(8, 6), comment='成分比例相似度(高精度)')
    preservatives_similarity = Column(DECIMAL(8, 6), comment='防腐剂相似度(高精度)')
    emulsifiers_similarity = Column(DECIMAL(8, 6), comment='乳化剂相似度(高精度)')
    thickeners_similarity = Column(DECIMAL(8, 6), comment='增稠剂相似度(高精度)')
    common_ingredients_count = Column(Integer, comment='共同成分数量')
    total_ingredients_count = Column(Integer, comment='总成分数量')
    match_details = Column(Text, comment='匹配详情JSON')
    algorithm_version = Column(String(50), comment='算法版本')
    algorithm_parameters = Column(Text, comment='算法参数JSON')
    match_date = Column(DateTime, default=datetime.now)

    # 关系
    source_formula = relationship("FormulasToBeMatched", foreign_keys=[source_formula_id])
    target_formula = relationship("Formulas", foreign_keys=[target_formula_id])


# ==================== 系统支持表组 ====================

class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text)
    description = Column(String(500))
    config_type = Column(String(50), default='string')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==================== 双配方库处理工具类 ====================

class SystemConfigManager:
    """系统配置管理器"""

    @staticmethod
    def get_category_weights(session) -> Dict[str, float]:
        """获取分类权重配置"""
        try:
            default_weights = {
                '防腐剂': 0.35,
                '乳化剂': 0.15,
                '增稠剂': 0.15,
                '抗氧化剂': 0.1,
                '表面活性剂': 0.1,
                '其他': 0.15
            }

            weights = {}
            for category, default_value in default_weights.items():
                config_key = f"category_weight_{category}"
                config = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key,
                    SystemConfig.is_active == True
                ).first()

                if config:
                    try:
                        weights[category] = float(config.config_value)
                    except (ValueError, TypeError):
                        weights[category] = default_value
                else:
                    weights[category] = default_value

            return weights

        except Exception as e:
            logger.error(f"获取分类权重配置失败: {e}")
            # 返回默认权重
            return {
                '防腐剂': 0.35,
                '乳化剂': 0.15,
                '增稠剂': 0.15,
                '抗氧化剂': 0.1,
                '表面活性剂': 0.1,
                '其他': 0.15
            }

    @staticmethod
    def set_category_weights(session, weights: Dict[str, float]):
        """设置分类权重配置"""
        try:
            for category, weight in weights.items():
                config_key = f"category_weight_{category}"
                config = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key
                ).first()

                if config:
                    config.config_value = str(weight)
                    config.updated_at = datetime.now()
                else:
                    config = SystemConfig(
                        config_key=config_key,
                        config_value=str(weight),
                        description=f'{category}分类权重',
                        config_type='float'
                    )
                    session.add(config)

            session.commit()
            logger.info(f"分类权重配置已更新: {weights}")

        except Exception as e:
            session.rollback()
            logger.error(f"设置分类权重配置失败: {e}")
            raise e

    @staticmethod
    def get_matching_parameters(session) -> Dict[str, float]:
        """获取匹配算法参数"""
        try:
            default_params = {
                'composition_weight': 0.8,
                'proportion_weight': 0.2,
                'compound_threshold': 0.6,
                'min_similarity_threshold': 0.0
            }

            params = {}
            for param_key, default_value in default_params.items():
                config_key = f"matching_{param_key}"
                config = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key,
                    SystemConfig.is_active == True
                ).first()

                if config:
                    try:
                        params[param_key] = float(config.config_value)
                    except (ValueError, TypeError):
                        params[param_key] = default_value
                else:
                    params[param_key] = default_value

            return params

        except Exception as e:
            logger.error(f"获取匹配参数配置失败: {e}")
            return {
                'composition_weight': 0.8,
                'proportion_weight': 0.2,
                'compound_threshold': 0.6,
                'min_similarity_threshold': 0.0
            }

    @staticmethod
    def set_matching_parameters(session, params: Dict[str, float]):
        """设置匹配算法参数"""
        try:
            param_descriptions = {
                'composition_weight': '成分组成相似度权重',
                'proportion_weight': '成分比例相似度权重',
                'compound_threshold': '复配匹配成功阈值',
                'min_similarity_threshold': '最小相似度阈值'
            }

            for param_key, value in params.items():
                config_key = f"matching_{param_key}"
                config = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key
                ).first()

                if config:
                    config.config_value = str(value)
                    config.updated_at = datetime.now()
                else:
                    config = SystemConfig(
                        config_key=config_key,
                        config_value=str(value),
                        description=param_descriptions.get(param_key, f'{param_key}参数'),
                        config_type='float'
                    )
                    session.add(config)

            session.commit()
            logger.info(f"匹配算法参数已更新: {params}")

        except Exception as e:
            session.rollback()
            logger.error(f"设置匹配算法参数失败: {e}")
            raise e

    @staticmethod
    def get_product_types(session) -> Dict[str, List[str]]:
        """获取产品类型配置"""
        try:
            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == "product_types",
                SystemConfig.is_active == True
            ).first()

            if config:
                import json
                try:
                    return json.loads(config.config_value)
                except (json.JSONDecodeError, TypeError):
                    pass

            # 返回默认产品类型
            return {
                '驻留类': ['护肤水', '护肤霜膏乳', '涂抹面膜', '片状面膜', '凝胶', '护肤精油', '护发精油'],
                '淋洗类': ['洗发水', '护发素', '沐浴露', '洗面霜膏乳', '洗面慕斯', '卸妆霜膏乳', '卸妆油',
                           '卸妆水'],
                '其他类': []
            }

        except Exception as e:
            logger.error(f"获取产品类型配置失败: {e}")
            # 返回默认产品类型
            return {
                '驻留类': ['护肤水', '护肤霜膏乳', '涂抹面膜', '片状面膜', '凝胶', '护肤精油', '护发精油'],
                '淋洗类': ['洗发水', '护发素', '沐浴露', '洗面霜膏乳', '洗面慕斯', '卸妆霜膏乳', '卸妆油',
                           '卸妆水'],
                '其他类': []
            }

    @staticmethod
    def set_product_types(session, product_types: Dict[str, List[str]]):
        """设置产品类型配置"""
        try:
            import json

            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == "product_types"
            ).first()

            config_value = json.dumps(product_types, ensure_ascii=False)

            if config:
                config.config_value = config_value
            else:
                config = SystemConfig(
                    config_key="product_types",
                    config_value=config_value,
                    description="产品类型及二级分类配置",
                    config_type='json'
                )
                session.add(config)

            session.commit()
            logger.info("产品类型配置更新成功")

        except Exception as e:
            session.rollback()
            logger.error(f"设置产品类型配置失败: {e}")
            raise e

    @staticmethod
    def initialize_default_config(session):
        """初始化默认配置"""
        try:
            # 初始化分类权重
            default_category_weights = {
                '防腐剂': 0.35,
                '乳化剂': 0.15,
                '增稠剂': 0.15,
                '抗氧化剂': 0.1,
                '表面活性剂': 0.1,
                '其他': 0.15
            }

            for category, weight in default_category_weights.items():
                config_key = f"category_weight_{category}"
                existing = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key
                ).first()

                if not existing:
                    config = SystemConfig(
                        config_key=config_key,
                        config_value=str(weight),
                        description=f'{category}分类权重',
                        config_type='float'
                    )
                    session.add(config)

            # 初始化匹配算法参数
            default_matching_params = {
                'composition_weight': 0.8,
                'proportion_weight': 0.2,
                'compound_threshold': 0.6,
                'min_similarity_threshold': 0.0
            }

            param_descriptions = {
                'composition_weight': '成分组成相似度权重',
                'proportion_weight': '成分比例相似度权重',
                'compound_threshold': '复配匹配成功阈值',
                'min_similarity_threshold': '最小相似度阈值'
            }

            for param_key, value in default_matching_params.items():
                config_key = f"matching_{param_key}"
                existing = session.query(SystemConfig).filter(
                    SystemConfig.config_key == config_key
                ).first()

                if not existing:
                    config = SystemConfig(
                        config_key=config_key,
                        config_value=str(value),
                        description=param_descriptions.get(param_key, f'{param_key}参数'),
                        config_type='float'
                    )
                    session.add(config)

            # 初始化产品类型配置
            product_types_key = "product_types"
            existing_product_types = session.query(SystemConfig).filter(
                SystemConfig.config_key == product_types_key
            ).first()

            if not existing_product_types:
                import json
                default_product_types = {
                    '驻留类': ['护肤水', '护肤霜膏乳', '涂抹面膜', '片状面膜', '凝胶', '护肤精油', '护发精油'],
                    '淋洗类': ['洗发水', '护发素', '沐浴露', '洗面霜膏乳', '洗面慕斯', '卸妆霜膏乳', '卸妆油',
                               '卸妆水'],
                    '其他类': []
                }

                config = SystemConfig(
                    config_key=product_types_key,
                    config_value=json.dumps(default_product_types, ensure_ascii=False),
                    description='产品类型及二级分类配置',
                    config_type='json'
                )
                session.add(config)

            session.commit()
            logger.info("默认配置初始化完成")

        except Exception as e:
            session.rollback()
            logger.error(f"初始化默认配置失败: {e}")
            raise e

    @staticmethod
    def load_system_config():
        """从配置文件加载系统配置"""
        try:
            import configparser
            config = configparser.ConfigParser()
            # 修正路径：项目根目录的system_config.ini
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            config_path = os.path.join(project_root, 'system_config.ini')
            
            if os.path.exists(config_path):
                config.read(config_path, encoding='utf-8')
                logger.info(f"成功加载系统配置: {config_path}")
                return config
            else:
                logger.warning(f"配置文件不存在: {config_path}")
                return None
        except Exception as e:
            logger.error(f"加载系统配置失败: {e}")
            return None

    @staticmethod
    def initialize_admin_user(session):
        """初始化管理员用户"""
        try:
            # 从配置文件获取管理员信息
            config = SystemConfigManager.load_system_config()
            if config and 'admin' in config:
                admin_username = config.get('admin', 'username', fallback='admin')
                admin_password = config.get('admin', 'password', fallback='yanglinbin0106')
            else:
                admin_username = 'admin'
                admin_password = 'yanglinbin0106'
                logger.warning("使用默认管理员配置")

            # 检查是否已存在管理员用户
            admin_user = session.query(Users).filter(
                Users.username == admin_username
            ).first()

            if not admin_user:
                import hashlib
                # 创建管理员用户
                password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
                admin_user = Users(
                    username=admin_username,
                    password=password_hash,
                    role='admin'
                )
                session.add(admin_user)
                session.commit()
                logger.info(f"管理员用户初始化完成: {admin_username}")
            else:
                # 更新现有管理员密码（如果配置文件有变化）
                import hashlib
                new_password_hash = hashlib.sha256(admin_password.encode()).hexdigest()
                if admin_user.password != new_password_hash:
                    admin_user.password = new_password_hash
                    session.commit()
                    logger.info(f"管理员密码已更新: {admin_username}")
                else:
                    logger.info(f"管理员用户已存在: {admin_username}")

        except Exception as e:
            session.rollback()
            logger.error(f"初始化管理员用户失败: {e}")
            raise e

    @staticmethod
    def authenticate_user(session, username: str, password: str) -> Optional[Users]:
        """验证用户登录"""
        try:
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            user = session.query(Users).filter(
                Users.username == username,
                Users.password == password_hash,
                Users.is_active == True
            ).first()

            if user:
                # 更新最后登录时间
                user.last_login = datetime.now()
                session.commit()

            return user

        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None

    @staticmethod
    def create_user(session, username: str, password: str, role: str = 'user') -> Users:
        """创建新用户"""
        try:
            import re
            import hashlib

            # 验证用户名格式（1-16位英文数字符号）
            if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{1,16}$', username):
                raise ValueError("用户名只能包含英文、数字和符号，长度1-16位")

            # 验证密码格式（4-16位）
            if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,16}$', password):
                raise ValueError("密码只能包含英文、数字和符号，长度4-16位")

            # 检查用户名是否已存在
            existing_user = session.query(Users).filter(Users.username == username).first()
            if existing_user:
                raise ValueError("用户名已存在")

            # 创建用户
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = Users(
                username=username,
                password=password_hash,
                role=role
            )

            session.add(user)
            session.commit()

            logger.info(f"用户创建成功: {username}")
            return user

        except Exception as e:
            session.rollback()
            logger.error(f"创建用户失败: {e}")
            raise e

    @staticmethod
    def get_product_type_mappings(session) -> Dict[str, str]:
        """获取产品类型映射表"""
        try:
            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == "product_type_mappings",
                SystemConfig.is_active == True
            ).first()

            if config:
                import json
                try:
                    return json.loads(config.config_value)
                except (json.JSONDecodeError, TypeError):
                    pass

            # 返回空映射表
            return {}

        except Exception as e:
            logger.error(f"获取产品类型映射表失败: {e}")
            return {}

    @staticmethod
    def set_product_type_mappings(session, mappings: Dict[str, str]):
        """设置产品类型映射表"""
        try:
            import json

            config = session.query(SystemConfig).filter(
                SystemConfig.config_key == "product_type_mappings"
            ).first()

            config_value = json.dumps(mappings, ensure_ascii=False)

            if config:
                config.config_value = config_value
                config.updated_at = datetime.now()
            else:
                config = SystemConfig(
                    config_key="product_type_mappings",
                    config_value=config_value,
                    description="产品类型映射表，用于将不规则命名映射到标准产品类型",
                    config_type='json'
                )
                session.add(config)

            session.commit()
            logger.info(f"产品类型映射表更新成功: {len(mappings)}条映射")

        except Exception as e:
            session.rollback()
            logger.error(f"设置产品类型映射表失败: {e}")
            raise e

    @staticmethod
    def add_product_type_mapping(session, from_name: str, to_product_type: str):
        """添加单个产品类型映射"""
        try:
            # 获取现有映射表
            current_mappings = SystemConfigManager.get_product_type_mappings(session)
            
            # 添加新映射
            current_mappings[from_name] = to_product_type
            
            # 保存更新后的映射表
            SystemConfigManager.set_product_type_mappings(session, current_mappings)
            logger.info(f"添加产品类型映射成功: '{from_name}' → '{to_product_type}'")

        except Exception as e:
            logger.error(f"添加产品类型映射失败: {e}")
            raise e

    @staticmethod
    def delete_product_type_mapping(session, from_name: str):
        """删除单个产品类型映射"""
        try:
            # 获取现有映射表
            current_mappings = SystemConfigManager.get_product_type_mappings(session)
            
            # 删除指定映射
            if from_name in current_mappings:
                del current_mappings[from_name]
                
                # 保存更新后的映射表
                SystemConfigManager.set_product_type_mappings(session, current_mappings)
                logger.info(f"删除产品类型映射成功: '{from_name}'")
                return True
            else:
                logger.warning(f"要删除的映射不存在: '{from_name}'")
                return False

        except Exception as e:
            logger.error(f"删除产品类型映射失败: {e}")
            raise e


class DualFormulaLibraryHandler:
    """双配方库处理工具"""

    @staticmethod
    def get_formula_structure(formula_id: int, session, table_type='reference') -> dict:
        """获取配方的完整结构（单配+复配）"""
        from decimal import Decimal
        
        def safe_float(value):
            """安全转换Decimal为float"""
            if value is None:
                return 0.0
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (int, float)):
                return float(value)
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
                
        # 根据表类型选择对应的模型
        if table_type == 'reference':
            IngredientModel = FormulaIngredients
        else:  # to_be_matched
            IngredientModel = FormulaIngredientsToBeMatched

        # 获取所有配料
        all_ingredients = session.query(IngredientModel).filter(
            IngredientModel.formula_id == formula_id
        ).order_by(IngredientModel.ingredient_id, IngredientModel.ingredient_sequence).all()

        # 按配料ID分组
        ingredients_dict = {}
        for ingredient in all_ingredients:
            ingredient_id = ingredient.ingredient_id
            if ingredient_id not in ingredients_dict:
                ingredients_dict[ingredient_id] = []
            ingredients_dict[ingredient_id].append(ingredient)

        # 构建结构化数据
        formula_structure = {
            'formula_id': formula_id,
            'table_type': table_type,
            'ingredients': [],
            'compound_ingredients': [],
            'single_ingredients': []
        }

        for ingredient_id, components in ingredients_dict.items():
            if len(components) == 1:
                # 单配
                component = components[0]
                ingredient_data = {
                    'ingredient_id': ingredient_id,
                    'type': 'single',
                    'chinese_name': component.standard_chinese_name or '',
                    'inci_name': component.inci_name or '',
                    'content': safe_float(component.ingredient_content),  # 修复：安全转换Decimal
                    'actual_content': safe_float(component.actual_component_content),  # 修复：安全转换Decimal
                    'purpose': component.purpose or '其他',  # 添加purpose字段
                    'catalog_id': component.catalog_id  # 添加catalog_id字段
                }
                formula_structure['single_ingredients'].append(ingredient_data)
            else:
                # 复配
                compound_data = {
                    'ingredient_id': ingredient_id,
                    'type': 'compound',
                    'total_content': safe_float(components[0].ingredient_content),  # 修复：安全转换Decimal
                    'purpose': components[0].purpose or '其他',  # 添加复配的purpose字段
                    'components': []
                }

                for component in components:
                    component_data = {
                        'sequence': component.ingredient_sequence,
                        'chinese_name': component.standard_chinese_name or '',
                        'inci_name': component.inci_name or '',
                        'component_content': safe_float(component.component_content),  # 修复：安全转换Decimal
                        'actual_content': safe_float(component.actual_component_content),  # 修复：安全转换Decimal
                        'catalog_id': component.catalog_id  # 添加catalog_id字段
                    }
                    compound_data['components'].append(component_data)

                formula_structure['compound_ingredients'].append(compound_data)

        formula_structure['ingredients'] = formula_structure['single_ingredients'] + formula_structure[
            'compound_ingredients']

        return formula_structure


def create_updated_database_schema(database_url: str):
    """创建更新的数据库架构"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


if __name__ == "__main__":
    print("🏗️  更新的数据库架构 - 双配方库支持")
    print("📋 表结构:")
    print("  配方库表组:")
    print("    - formulas (配方库主表)")
    print("    - formula_ingredients (配方库成分表)")
    print("  待匹配表组:")
    print("    - formulas_to_be_matched (待匹配配方主表)")
    print("    - formula_ingredients_to_be_matched (待匹配配方成分表)")
    print("  支持表组:")
    print("    - ingredient_catalog (原料目录)")
    print("    - formula_match_records (匹配记录)")
    print("    - compound_systems (复配体系)")
    print("    - system_config (系统配置)")
    print("    - data_import_logs (导入日志)")
