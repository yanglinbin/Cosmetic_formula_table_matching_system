#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置API路由
"""

import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backend.dependencies import get_db, get_current_user
from src.backend.sql.mysql_models import SystemConfig, SystemConfigManager, Users

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["系统配置"])


class CategoryWeightsRequest(BaseModel):
    防腐剂: float
    乳化剂: float
    增稠剂: float
    抗氧化剂: float
    表面活性剂: float
    其他: float


class MatchingParametersRequest(BaseModel):
    composition_weight: float
    proportion_weight: float
    compound_threshold: float
    min_similarity_threshold: float


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db)):
    """获取系统统计信息 - 双配方库版本"""
    try:
        from src.backend.sql.mysql_models import (
            IngredientCatalog, Formulas, FormulaIngredients,
            FormulasToBeMatched, FormulaIngredientsToBeMatched, FormulaMatchRecord
        )
        
        stats = {
            "ingredient_catalog_count": db.query(IngredientCatalog).count(),
            "reference_formulas_count": db.query(Formulas).count(),
            "reference_ingredients_count": db.query(FormulaIngredients).count(),
            "to_match_formulas_count": db.query(FormulasToBeMatched).count(),
            "to_match_ingredients_count": db.query(FormulaIngredientsToBeMatched).count(),
            "match_records_count": db.query(FormulaMatchRecord).count(),
            "system_configs_count": db.query(SystemConfig).count()
        }
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")


@router.get("/config/category-weights")
async def get_category_weights(db: Session = Depends(get_db)):
    """获取分类权重配置"""
    try:
        weights = SystemConfigManager.get_category_weights(db)
        return JSONResponse(content={"success": True, "data": weights})
    except Exception as e:
        logger.error(f"获取分类权重配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类权重配置失败: {str(e)}")


@router.put("/config/category-weights")
async def update_category_weights(request: CategoryWeightsRequest, db: Session = Depends(get_db)):
    """更新分类权重配置"""
    try:
        weights = {
            '防腐剂': request.防腐剂,
            '乳化剂': request.乳化剂,
            '增稠剂': request.增稠剂,
            '抗氧化剂': request.抗氧化剂,
            '表面活性剂': request.表面活性剂,
            '其他': request.其他
        }

        # 验证权重总和是否为1.0（允许小误差）
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail=f"权重总和必须为1.0，当前为{total_weight:.3f}"
            )

        SystemConfigManager.set_category_weights(db, weights)
        logger.info(f"分类权重配置已更新: {weights}")

        return JSONResponse(content={
            "success": True,
            "message": "分类权重配置更新成功",
            "data": weights
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新分类权重配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新分类权重配置失败: {str(e)}")


@router.get("/config/matching-parameters")
async def get_matching_parameters(db: Session = Depends(get_db)):
    """获取匹配算法参数"""
    try:
        params = SystemConfigManager.get_matching_parameters(db)
        return JSONResponse(content={"success": True, "data": params})
    except Exception as e:
        logger.error(f"获取匹配参数配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取匹配参数配置失败: {str(e)}")


@router.put("/config/matching-parameters")
async def update_matching_parameters(request: MatchingParametersRequest, db: Session = Depends(get_db)):
    """更新匹配算法参数"""
    try:
        params = {
            'composition_weight': request.composition_weight,
            'proportion_weight': request.proportion_weight,
            'compound_threshold': request.compound_threshold,
            'min_similarity_threshold': request.min_similarity_threshold
        }

        # 验证组成权重和比例权重之和为1.0
        if abs(params['composition_weight'] + params['proportion_weight'] - 1.0) > 0.01:
            raise HTTPException(
                status_code=400,
                detail="组成权重和比例权重之和必须为1.0"
            )

        # 验证阈值范围
        if not (0.0 <= params['compound_threshold'] <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="复配匹配阈值必须在0.0-1.0之间"
            )

        if not (0.0 <= params['min_similarity_threshold'] <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="最小相似度阈值必须在0.0-1.0之间"
            )

        SystemConfigManager.set_matching_parameters(db, params)
        logger.info(f"匹配算法参数已更新: {params}")

        return JSONResponse(content={
            "success": True,
            "message": "匹配算法参数更新成功",
            "data": params
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新匹配参数配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新匹配参数配置失败: {str(e)}")


@router.get("/config/product-types")
async def get_product_types(db: Session = Depends(get_db)):
    """获取产品类型配置"""
    try:
        product_types = SystemConfigManager.get_product_types(db)

        result = {
            "success": True,
            "data": product_types,
            "message": "获取产品类型配置成功"
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"获取产品类型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取产品类型配置失败: {str(e)}")


@router.put("/config/product-types")
async def set_product_types(
        request: dict,
        db: Session = Depends(get_db)
):
    """设置产品类型配置"""
    try:
        # 验证请求数据
        if not isinstance(request, dict):
            raise HTTPException(status_code=400, detail="请求数据格式错误")

        # 验证数据结构
        for category, subcategories in request.items():
            if not isinstance(category, str):
                raise HTTPException(status_code=400, detail="分类名称必须是字符串")
            if not isinstance(subcategories, list):
                raise HTTPException(status_code=400, detail="二级分类必须是数组")
            for subcategory in subcategories:
                if not isinstance(subcategory, str):
                    raise HTTPException(status_code=400, detail="二级分类名称必须是字符串")

        SystemConfigManager.set_product_types(db, request)

        result = {
            "success": True,
            "message": "产品类型配置更新成功"
        }

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"设置产品类型配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置产品类型配置失败: {str(e)}")


@router.post("/config/initialize")
async def initialize_system_config(db: Session = Depends(get_db)):
    """初始化系统配置"""
    try:
        SystemConfigManager.initialize_default_config(db)
        logger.info("系统配置初始化完成")

        return JSONResponse(content={
            "success": True,
            "message": "系统配置初始化完成"
        })

    except Exception as e:
        logger.error(f"初始化系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化系统配置失败: {str(e)}")


class ProductTypeMappingRequest(BaseModel):
    from_name: str
    to_product_type: str


class ProductTypeMappingDeleteRequest(BaseModel):
    from_name: str


@router.get("/config/product-type-mappings")
async def get_product_type_mappings(db: Session = Depends(get_db)):
    """获取产品类型映射表"""
    try:
        mappings = SystemConfigManager.get_product_type_mappings(db)
        
        return JSONResponse(content={
            "success": True,
            "data": mappings,
            "message": f"获取产品类型映射表成功，共{len(mappings)}条映射"
        })

    except Exception as e:
        logger.error(f"获取产品类型映射表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取产品类型映射表失败: {str(e)}")


@router.post("/config/product-type-mappings")
async def add_product_type_mapping(
    request: ProductTypeMappingRequest, 
    db: Session = Depends(get_db)
):
    """添加产品类型映射"""
    try:
        SystemConfigManager.add_product_type_mapping(
            db, 
            request.from_name, 
            request.to_product_type
        )
        
        return JSONResponse(content={
            "success": True,
            "message": f"映射添加成功：'{request.from_name}' → '{request.to_product_type}'"
        })

    except Exception as e:
        logger.error(f"添加产品类型映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加产品类型映射失败: {str(e)}")


@router.delete("/config/product-type-mappings")
async def delete_product_type_mapping(
    request: ProductTypeMappingDeleteRequest, 
    db: Session = Depends(get_db)
):
    """删除产品类型映射"""
    try:
        success = SystemConfigManager.delete_product_type_mapping(db, request.from_name)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"映射删除成功：'{request.from_name}'"
            })
        else:
            return JSONResponse(content={
                "success": False,
                "message": f"映射不存在：'{request.from_name}'"
            })

    except Exception as e:
        logger.error(f"删除产品类型映射失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除产品类型映射失败: {str(e)}")


@router.put("/config/product-type-mappings")
async def set_product_type_mappings(
    request: dict,
    db: Session = Depends(get_db)
):
    """批量设置产品类型映射表"""
    try:
        # 验证请求数据格式
        if not isinstance(request, dict):
            raise ValueError("请求数据格式错误，应为映射字典")
        
        # 验证每个映射的值都是字符串
        for key, value in request.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("映射的键值都必须是字符串")
        
        SystemConfigManager.set_product_type_mappings(db, request)
        
        return JSONResponse(content={
            "success": True,
            "message": f"产品类型映射表更新成功，共{len(request)}条映射"
        })

    except Exception as e:
        logger.error(f"设置产品类型映射表失败: {e}")
        raise HTTPException(status_code=500, detail=f"设置产品类型映射表失败: {str(e)}")


# ==========================================
# 用户管理相关API
# ==========================================

class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = 'user'


class UserUpdateRequest(BaseModel):
    username: str = None
    password: str = None
    role: str = None
    is_active: bool = None


def check_admin_permission(current_user: Users = Depends(get_current_user)):
    """检查管理员权限"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    current_user: Users = Depends(check_admin_permission)
):
    """获取所有用户列表"""
    try:
        users = db.query(Users).all()
        users_data = []
        
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        return JSONResponse(content={
            "success": True,
            "data": users_data,
            "message": f"获取用户列表成功，共{len(users_data)}个用户"
        })
        
    except Exception as e:
        logger.error(f"获取用户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {str(e)}")


@router.post("/users")
async def create_user(
    request: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(check_admin_permission)
):
    """创建新用户"""
    try:
        user = SystemConfigManager.create_user(
            db, 
            request.username, 
            request.password, 
            request.role
        )
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "message": f"用户创建成功: {user.username}"
        })
        
    except ValueError as e:
        return JSONResponse(content={"success": False, "message": str(e)}, status_code=400)
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建用户失败: {str(e)}")


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(check_admin_permission)
):
    """更新用户信息"""
    try:
        # 获取要更新的用户
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不允许管理员修改自己的角色（防止锁定）
        if user.id == current_user.id and request.role and request.role != 'admin':
            raise HTTPException(status_code=400, detail="不能修改自己的管理员权限")
        
        updated_fields = []
        
        # 更新用户名
        if request.username and request.username != user.username:
            # 检查用户名是否已存在
            existing_user = db.query(Users).filter(
                Users.username == request.username, 
                Users.id != user_id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已存在")
            user.username = request.username
            updated_fields.append("用户名")
        
        # 更新密码
        if request.password:
            import hashlib
            user.password = hashlib.sha256(request.password.encode()).hexdigest()
            updated_fields.append("密码")
        
        # 更新角色
        if request.role and request.role != user.role:
            user.role = request.role
            updated_fields.append("角色")
        
        # 更新激活状态
        if request.is_active is not None and request.is_active != user.is_active:
            # 不允许停用自己的账户
            if user.id == current_user.id and not request.is_active:
                raise HTTPException(status_code=400, detail="不能停用自己的账户")
            user.is_active = request.is_active
            updated_fields.append("激活状态")
        
        if updated_fields:
            db.commit()
            message = f"用户 {user.username} 更新成功，已更新: {', '.join(updated_fields)}"
        else:
            message = "没有需要更新的字段"
        
        return JSONResponse(content={
            "success": True,
            "data": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            },
            "message": message
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新用户失败: {str(e)}")


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(check_admin_permission)
):
    """删除用户"""
    try:
        # 获取要删除的用户
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不允许删除自己
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="不能删除自己的账户")
        
        # 不允许删除最后一个管理员
        if user.role == 'admin':
            admin_count = db.query(Users).filter(Users.role == 'admin').count()
            if admin_count <= 1:
                raise HTTPException(status_code=400, detail="不能删除最后一个管理员账户")
        
        username = user.username
        db.delete(user)
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"用户 {username} 删除成功"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除用户失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除用户失败: {str(e)}")


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(check_admin_permission)
):
    """重置用户密码"""
    try:
        # 获取要重置密码的用户
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 验证密码格式
        import re
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,16}$', password):
            raise HTTPException(status_code=400, detail="密码只能包含英文、数字和符号，长度4-16位")
        
        # 更新密码
        import hashlib
        user.password = hashlib.sha256(password.encode()).hexdigest()
        db.commit()
        
        return JSONResponse(content={
            "success": True,
            "message": f"用户 {user.username} 密码重置成功"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"重置用户密码失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置用户密码失败: {str(e)}")