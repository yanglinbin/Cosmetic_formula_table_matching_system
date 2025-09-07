#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
化妆品配方表匹配系统 - 模块化版本
主程序入口
"""

import logging
import sys
import uvicorn
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.backend.app_factory import get_app

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    try:
        # 创建应用实例
        app = get_app()
        
        # 打印启动信息
        print_startup_info()
        
        # 启动Web服务器
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000, 
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


def print_startup_info():
    """打印启动信息"""
    print("🚀 启动化妆品配方表匹配系统 - 模块化版本")
    print("=" * 60)
    print("📊 数据库架构: 双配方库 (配方库 + 待匹配库)")
    print("🌐 Web界面: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("📚 配方库管理: http://localhost:8000/reference-library")
    print("🔍 配方匹配: http://localhost:8000/upload-match")
    print("⚙️ 系统配置: http://localhost:8000/system-config")
    print("=" * 60)
    print("🏗️ 架构特性:")
    print("  ✅ 模块化重构 - 代码结构清晰")
    print("  ✅ 职责分离 - API与页面分离")
    print("  ✅ 依赖注入 - 统一管理依赖")
    print("  ✅ 配置管理 - 支持配置文件")
    print("  ✅ 错误处理 - 完善的异常处理")
    print("=" * 60)


if __name__ == "__main__":
    main()
