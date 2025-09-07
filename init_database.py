#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
手动执行数据库创建和初始化
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.sql.mysql_config import MySQLManager
from src.backend.sql.mysql_models import SystemConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主初始化函数"""
    print("🏗️ 化妆品配方表匹配系统 - 数据库初始化")
    print("=" * 50)
    
    try:
        # 创建数据库管理器
        db_manager = MySQLManager()
        
        # 1. 创建数据库
        print("📊 步骤 1: 创建数据库...")
        if not db_manager.create_database():
            print("❌ 数据库创建失败，请检查MySQL连接配置")
            return False
        
        # 2. 连接数据库
        print("🔗 步骤 2: 连接数据库...")
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return False
        
        # 3. 创建所有表
        print("🏗️ 步骤 3: 创建数据表结构...")
        if not db_manager.create_tables():
            print("❌ 数据表创建失败")
            return False
        
        # 4. 初始化系统配置
        print("⚙️ 步骤 4: 初始化系统配置...")
        try:
            session = db_manager.get_session()
            
            # 初始化默认配置
            SystemConfigManager.initialize_default_config(session)
            print("✅ 系统配置初始化完成")
            
            # 初始化管理员用户
            SystemConfigManager.initialize_admin_user(session)
            print("✅ 管理员用户初始化完成")
            
            session.close()
            
        except Exception as e:
            print(f"❌ 系统配置初始化失败: {e}")
            return False
        
        # 5. 验证初始化结果
        print("🔍 步骤 5: 验证初始化结果...")
        try:
            session = db_manager.get_session()
            
            # 检查表是否存在
            from src.backend.sql.mysql_models import Users, SystemConfig, Formulas
            
            user_count = session.query(Users).count()
            config_count = session.query(SystemConfig).count()
            
            print(f"📊 数据验证结果:")
            print(f"  - 用户表记录数: {user_count}")
            print(f"  - 配置表记录数: {config_count}")
            
            session.close()
            
        except Exception as e:
            print(f"⚠️ 数据验证失败: {e}")
        
        # 6. 完成
        print("🎉 数据库初始化完成！")
        print("=" * 50)
        print("✅ 所有步骤执行成功")
        print("🚀 现在可以启动应用程序:")
        print("   python main.py")
        print("📱 访问地址: http://localhost:8000")
        print("👤 管理员登录: 请查看 system_config.ini 中的管理员信息")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        print(f"❌ 初始化过程出现错误: {e}")
        return False
    
    finally:
        # 清理资源
        try:
            db_manager.close()
        except:
            pass


def check_requirements():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查必要的包
    required_packages = [
        'sqlalchemy', 'pymysql', 'pandas', 'numpy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要的Python包: {missing_packages}")
        print("💡 请运行: pip install -r requirements.txt")
        return False
    
    # 检查配置文件
    config_files = ['mysql_config.ini', 'system_config.ini']
    missing_files = []
    
    for config_file in config_files:
        if not Path(config_file).exists():
            missing_files.append(config_file)
    
    if missing_files:
        print(f"❌ 缺少配置文件: {missing_files}")
        print("💡 请确保配置文件存在且配置正确")
        return False
    
    print("✅ 环境检查通过")
    return True


if __name__ == "__main__":
    print("🌟 化妆品配方表匹配系统 - 数据库初始化工具")
    print()
    
    # 环境检查
    if not check_requirements():
        sys.exit(1)
    
    print()
    
    # 执行初始化
    success = main()
    
    if success:
        print("\n🎊 数据库初始化成功！系统已准备就绪。")
        sys.exit(0)
    else:
        print("\n💥 数据库初始化失败！请检查错误信息并重试。")
        sys.exit(1)
