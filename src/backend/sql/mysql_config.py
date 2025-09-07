#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库配置和连接管理
"""

import os
import configparser
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logger = logging.getLogger(__name__)

def load_database_config():
    """从配置文件加载数据库配置"""
    config = configparser.ConfigParser()
    
    # 配置文件路径（项目根目录）
    project_root = Path(__file__).parent.parent.parent.parent  # 回到项目根目录
    config_file = project_root / 'mysql_config.ini'
    
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        logger.info(f"请从 mysql_config.ini.example 复制并修改配置文件")
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    try:
        config.read(config_file, encoding='utf-8')
        
        # 读取数据库配置
        db_config = {
            "host": config.get('database', 'host', fallback='localhost'),
            "port": config.getint('database', 'port', fallback=3306),
            "username": config.get('database', 'username'),
            "password": config.get('database', 'password'),
            "database": config.get('database', 'database'),
            "charset": config.get('database', 'charset', fallback='utf8mb4')
        }
        
        # 验证必需配置项
        required_fields = ['username', 'password', 'database']
        for field in required_fields:
            if not db_config[field]:
                raise ValueError(f"配置文件中缺少必需项: {field}")
        
        logger.info(f"成功加载数据库配置: {config_file}")
        return db_config
        
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}")
        raise

# 加载数据库配置
try:
    MYSQL_CONFIG = load_database_config()
except Exception as e:
    logger.warning(f"无法加载配置文件，使用默认配置: {e}")
    # 保留默认配置作为后备
    MYSQL_CONFIG = {
        "host": "localhost",
        "port": 3306,
        "username": "root",
        "password": "yanglinbin0106",
        "database": "cosmetic_formula_db",
        "charset": "utf8mb4"
    }


def get_mysql_url():
    """构建MySQL连接URL"""
    return f"mysql+pymysql://{MYSQL_CONFIG['username']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}/{MYSQL_CONFIG['database']}?charset={MYSQL_CONFIG['charset']}"


def get_mysql_url_without_db():
    """不包含数据库名的连接URL（用于创建数据库）"""
    return f"mysql+pymysql://{MYSQL_CONFIG['username']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}?charset={MYSQL_CONFIG['charset']}"


# 注意：数据库模型已移动到 mysql_models.py 文件中
# 此处保留Base声明以保持向后兼容
Base = declarative_base()


class MySQLManager:
    """MySQL数据库管理器"""

    def __init__(self):
        self.engine = None
        self.SessionLocal = None

    def create_database(self):
        """创建数据库"""
        try:
            # 连接MySQL服务器（不指定数据库）
            engine_without_db = create_engine(get_mysql_url_without_db())

            with engine_without_db.connect() as conn:
                # 创建数据库
                conn.execute(text(
                    f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                logger.info(f"✅ 数据库 {MYSQL_CONFIG['database']} 创建成功")

            engine_without_db.dispose()
            return True

        except Exception as e:
            logger.error(f"❌ 创建数据库失败: {e}")
            return False

    def connect(self):
        """连接数据库"""
        try:
            self.engine = create_engine(
                get_mysql_url(),
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # 设置为True可以看到SQL语句
            )

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

            # 测试连接
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("✅ MySQL数据库连接成功")

            return True

        except Exception as e:
            logger.error(f"❌ 连接MySQL数据库失败: {e}")
            return False

    def create_tables(self):
        """创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ 数据库表创建成功")
            return True
        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            return False

    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()

    def init_basic_config(self):
        """初始化基本系统配置（仅配置数据，不包含示例数据）"""
        try:
            from .mysql_models import SystemConfig, SystemConfigManager
            session = self.get_session()

            # 使用SystemConfigManager来初始化配置
            SystemConfigManager.initialize_default_config(session)
            session.close()

            logger.info("✅ 基本配置初始化成功")

        except Exception as e:
            logger.error(f"❌ 初始化基本配置失败: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()

    def close(self):
        """关闭连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("MySQL连接已关闭")


def test_mysql_connection():
    """测试MySQL连接"""
    print("🔍 测试MySQL连接...")
    print("=" * 40)

    # 提示配置信息
    print("当前MySQL配置:")
    print(f"  主机: {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    print(f"  用户: {MYSQL_CONFIG['username']}")
    print(f"  数据库: {MYSQL_CONFIG['database']}")
    print()

    db_manager = MySQLManager()

    # 1. 创建数据库
    print("1. 创建数据库...")
    if not db_manager.create_database():
        print("❌ 数据库创建失败，请检查MySQL服务和配置")
        return False

    # 2. 连接数据库
    print("2. 连接数据库...")
    if not db_manager.connect():
        print("❌ 数据库连接失败")
        return False

    # 3. 创建表
    print("3. 创建数据表...")
    if not db_manager.create_tables():
        print("❌ 表创建失败")
        return False

    # 4. 初始化基本配置
    print("4. 初始化基本配置...")
    db_manager.init_basic_config()

    # 5. 验证数据库
    print("5. 验证数据库...")
    try:
        session = db_manager.get_session()

        # 验证表是否创建成功
        tables_check = True
        expected_tables = [
            'formulas', 'formula_ingredients', 'ingredient_catalog', 
            'formulas_to_be_matched', 'formula_ingredients_to_be_matched',
            'formula_match_records', 'system_config', 'users'
        ]
        for table in expected_tables:
            try:
                session.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
            except:
                print(f"  ❌ 表 {table} 不存在或无法访问")
                tables_check = False

        if tables_check:
            print("  ✅ 所有数据表创建成功")

            # 检查系统配置（使用mysql_models中的模型）
            try:
                from .mysql_models import SystemConfig
                config_count = session.query(SystemConfig).count()
                print(f"  系统配置: {config_count} 条")
            except Exception as e:
                print(f"  系统配置检查失败: {e}")

        session.close()

    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

    db_manager.close()

    print("\n✅ MySQL数据库配置完成！")
    print("\n📋 Navicat连接信息:")
    print(f"  连接名: 化妆品配方系统")
    print(f"  主机: {MYSQL_CONFIG['host']}")
    print(f"  端口: {MYSQL_CONFIG['port']}")
    print(f"  用户名: {MYSQL_CONFIG['username']}")
    print(f"  数据库: {MYSQL_CONFIG['database']}")

    return True


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    test_mysql_connection()
