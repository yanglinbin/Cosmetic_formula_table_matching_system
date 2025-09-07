#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证授权API路由
"""

import logging
from fastapi import APIRouter, HTTPException, Request, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backend.dependencies import get_db, get_current_user
from src.backend.sql.mysql_models import Users, SystemConfigManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...),
                db: Session = Depends(get_db)):
    """用户登录"""
    try:
        # 验证输入格式
        if not (1 <= len(username) <= 16):
            raise HTTPException(status_code=400, detail="用户名长度必须在1-16位之间")
        if not (4 <= len(password) <= 16):
            raise HTTPException(status_code=400, detail="密码长度必须在4-16位之间")

        # 验证用户
        user = SystemConfigManager.authenticate_user(db, username, password)
        if not user:
            return JSONResponse(content={"success": False, "message": "用户名或密码错误"})

        # 设置会话
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["role"] = user.role

        return JSONResponse(content={
            "success": True,
            "message": "登录成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return JSONResponse(content={"success": False, "message": "登录失败，请稍后重试"})


@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """用户注册"""
    try:
        # 创建用户
        user = SystemConfigManager.create_user(db, username, password)

        return JSONResponse(content={
            "success": True,
            "message": "注册成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "role": user.role
            }
        })

    except ValueError as e:
        return JSONResponse(content={"success": False, "message": str(e)})
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return JSONResponse(content={"success": False, "message": "注册失败，请稍后重试"})


@router.post("/logout")
async def logout(request: Request):
    """用户登出"""
    request.session.clear()
    return JSONResponse(content={"success": True, "message": "登出成功"})


@router.get("/user")
async def get_current_user_info(current_user: Users = Depends(get_current_user)):
    """获取当前用户信息"""
    if not current_user:
        raise HTTPException(status_code=401, detail="未登录")

    return JSONResponse(content={
        "success": True,
        "data": {
            "user_id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None
        }
    })


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user)
):
    """修改当前用户密码"""
    try:
        # 验证用户是否已登录
        if not current_user:
            raise HTTPException(status_code=401, detail="请先登录")

        # 验证新密码格式
        if not (4 <= len(new_password) <= 16):
            return JSONResponse(content={"success": False, "message": "新密码长度必须在4-16位之间"})

        # 验证密码确认
        if new_password != confirm_password:
            return JSONResponse(content={"success": False, "message": "两次输入的新密码不一致"})

        # 验证当前密码
        import hashlib
        current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
        if current_user.password != current_password_hash:
            return JSONResponse(content={"success": False, "message": "当前密码不正确"})

        # 检查新密码是否与当前密码相同
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        if current_user.password == new_password_hash:
            return JSONResponse(content={"success": False, "message": "新密码不能与当前密码相同"})

        # 更新密码
        current_user.password = new_password_hash
        db.commit()

        logger.info(f"用户 {current_user.username} (ID: {current_user.id}) 修改密码成功")

        return JSONResponse(content={
            "success": True,
            "message": "密码修改成功！"
        })

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"修改密码失败: {e}")
        return JSONResponse(content={"success": False, "message": "密码修改失败，请稍后重试"})
