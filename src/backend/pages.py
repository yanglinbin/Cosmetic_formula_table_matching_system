#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
页面路由模块
"""

import logging
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src.backend.dependencies import get_current_user, require_login, require_admin
from src.backend.sql.mysql_models import Users

logger = logging.getLogger(__name__)
router = APIRouter(tags=["页面"])

# 初始化模板引擎
templates = Jinja2Templates(directory="src/frontend/templates")


@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request, current_user: Users = Depends(get_current_user)):
    """登录页面"""
    # 如果用户已经登录，跳转到dashboard
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)

    # 使用Jinja2模板渲染登录页面
    template_data = {
        "request": request
    }

    return templates.TemplateResponse("login.html", template_data)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: Users = Depends(require_login)):
    """登录后的主页面"""
    # 业务逻辑：根据用户角色显示不同的导航和功能
    is_admin = current_user.role == 'admin'
    welcome_text = '作为管理员，您拥有系统的完整访问权限。' if is_admin else '欢迎使用系统进行配方分析和匹配。'

    # 准备模板数据
    template_data = {
        "request": request,
        "current_user": current_user,
        "is_admin": is_admin,
        "welcome_text": welcome_text
    }

    # 使用Jinja2模板渲染
    return templates.TemplateResponse("dashboard.html", template_data)


@router.get("/reference-library", response_class=HTMLResponse)
async def reference_library_page(request: Request, current_user: Users = Depends(require_login)):
    """配方库管理页面"""
    # 业务逻辑：根据用户角色显示不同的导航和功能
    is_admin = current_user.role == 'admin'

    # 准备模板数据
    template_data = {
        "request": request,
        "current_user": current_user,
        "is_admin": is_admin
    }

    # 使用Jinja2模板渲染
    return templates.TemplateResponse("reference-library.html", template_data)


@router.get("/upload-match", response_class=HTMLResponse)
async def upload_match_page(request: Request, current_user: Users = Depends(require_login)):
    """配方上传和匹配页面"""
    # 业务逻辑：根据用户角色显示不同的导航和功能
    is_admin = current_user.role == 'admin'

    # 准备模板数据
    template_data = {
        "request": request,
        "current_user": current_user,
        "is_admin": is_admin
    }

    # 使用Jinja2模板渲染
    return templates.TemplateResponse("upload-match.html", template_data)


@router.get("/system-config", response_class=HTMLResponse)
async def system_config_page(request: Request, current_user: Users = Depends(require_admin)):
    """系统配置页面"""
    # 业务逻辑：根据用户角色显示不同的导航和功能
    is_admin = current_user.role == 'admin'

    # 准备模板数据
    template_data = {
        "request": request,
        "current_user": current_user,
        "is_admin": is_admin
    }

    # 使用Jinja2模板渲染
    return templates.TemplateResponse("system-config.html", template_data)
