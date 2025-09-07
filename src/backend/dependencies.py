#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依赖注入和全局变量管理
"""

import logging
from typing import Optional
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

from src.backend.sql.mysql_config import get_mysql_url
from src.backend.sql.mysql_models import Users, SystemConfigManager

logger = logging.getLogger(__name__)

# 全局变量
_matching_engine = None
_engine = None
_SessionLocal = None


def get_matching_engine(db_session):
    """获取匹配引擎实例（单例模式）"""
    global _matching_engine
    if _matching_engine is None:
        from ..backend.dual_library_matching_engine import DualLibraryMatchingEngine
        _matching_engine = DualLibraryMatchingEngine()
        logger.info("匹配引擎初始化完成")
    return _matching_engine


def initialize_database():
    """初始化数据库连接"""
    global _engine, _SessionLocal
    
    if _engine is None:
        _engine = create_engine(get_mysql_url())
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        
        # 启动时自动初始化系统配置和管理员用户
        try:
            with _SessionLocal() as db:
                SystemConfigManager.initialize_default_config(db)
                SystemConfigManager.initialize_admin_user(db)
            logger.info("系统配置和管理员用户自动初始化完成")
        except Exception as e:
            logger.warning(f"系统配置自动初始化失败: {e}")
    
    return _engine, _SessionLocal


def get_db():
    """数据库依赖注入"""
    _, SessionLocal = initialize_database()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[Users]:
    """获取当前登录用户"""
    user_id = request.session.get("user_id")
    if user_id:
        return db.query(Users).filter(Users.id == user_id, Users.is_active == True).first()
    return None


def require_login(current_user: Users = Depends(get_current_user)) -> Users:
    """需要登录的依赖"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录，需要跳转到登录页面")
    return current_user


def require_admin(current_user: Users = Depends(require_login)) -> Users:
    """需要管理员权限的依赖"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
