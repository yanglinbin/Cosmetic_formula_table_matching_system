#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用工厂模块
"""

import logging
import configparser
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .dependencies import initialize_database

logger = logging.getLogger(__name__)


def get_session_timeout() -> int:
    """从配置文件读取会话超时时间"""
    try:
        config = configparser.ConfigParser()
        # 修正路径：项目根目录的system_config.ini
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        config_path = os.path.join(project_root, "system_config.ini")
        
        if os.path.exists(config_path):
            config.read(config_path, encoding='utf-8')
            session_timeout = config.getint('security', 'session_timeout', fallback=1800)
            logger.info(f"从配置文件读取会话超时时间: {session_timeout}秒 (路径: {config_path})")
            return session_timeout
        else:
            logger.warning(f"配置文件不存在: {config_path}，使用默认会话超时时间: 1800秒")
            return 1800
    except Exception as e:
        logger.error(f"读取会话超时配置失败: {e}，使用默认值: 1800秒")
        return 1800


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    # 创建FastAPI应用
    app = FastAPI(
        title="化妆品配方表匹配系统",
        description="Professional Cosmetic Formula Analysis & Matching Platform - Dual Library Edition",
        version="3.0.0"
    )

    # 配置中间件
    setup_middleware(app)
    
    # 挂载静态文件
    setup_static_files(app)
    
    # 初始化数据库
    initialize_database()
    
    # 注册路由
    register_routes(app)
    
    logger.info("FastAPI应用创建完成")
    return app


def setup_middleware(app: FastAPI):
    """配置中间件"""
    
    # CORS配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 读取会话超时配置
    session_timeout = get_session_timeout()
    
    # 会话中间件
    app.add_middleware(
        SessionMiddleware, 
        secret_key="your-secret-key-cosmetic-formula-system",
        max_age=session_timeout
    )
    
    logger.info(f"中间件配置完成，会话超时时间: {session_timeout}秒")


def setup_static_files(app: FastAPI):
    """挂载静态文件"""
    app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")
    logger.info("静态文件挂载完成")


def register_routes(app: FastAPI):
    """注册所有路由"""
    
    # 导入路由模块
    from src.backend.api.auth import router as auth_router
    from src.backend.api.reference_library import router as reference_router
    from src.backend.api.matching import router as matching_router
    from src.backend.api.system_config import router as config_router
    from src.backend.pages import router as pages_router
    
    # 注册API路由
    app.include_router(auth_router)
    app.include_router(reference_router)
    app.include_router(matching_router)
    app.include_router(config_router)
    
    # 注册页面路由
    app.include_router(pages_router)
    
    logger.info("路由注册完成")


def get_app() -> FastAPI:
    """获取应用实例（单例模式）"""
    return create_app()
