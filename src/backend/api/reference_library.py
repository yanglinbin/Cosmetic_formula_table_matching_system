#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
参考配方库API路由
"""

import os
import tempfile
import logging
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.backend.dependencies import get_db, require_login
from src.backend.sql.mysql_models import (
    Formulas, FormulaIngredients, IngredientCatalog, 
    FormulaMatchRecord, Users, DualFormulaLibraryHandler
)
from src.backend.formula_parser import FormulaParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["参考配方库"])


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


@router.get("/reference-library-stats")
async def get_reference_library_stats(db: Session = Depends(get_db)):
    """获取配方库管理统计信息"""
    try:
        # 配方总数
        total_formulas = db.query(func.count(Formulas.id)).scalar()

        # 成分总数
        total_ingredients = db.query(func.count(FormulaIngredients.id)).scalar()

        # 产品类型数量
        product_types_query = db.query(func.count(func.distinct(Formulas.product_type))).filter(
            Formulas.product_type.isnot(None),
            Formulas.product_type != ''
        ).scalar()

        # 产品类型列表
        product_type_list = db.query(func.distinct(Formulas.product_type)).filter(
            Formulas.product_type.isnot(None),
            Formulas.product_type != ''
        ).all()
        product_type_list = [item[0] for item in product_type_list if item[0]]

        # 客户数量
        customers_query = db.query(func.count(func.distinct(Formulas.customer))).filter(
            Formulas.customer.isnot(None),
            Formulas.customer != ''
        ).scalar()

        # 客户列表
        customer_list = db.query(func.distinct(Formulas.customer)).filter(
            Formulas.customer.isnot(None),
            Formulas.customer != ''
        ).all()
        customer_list = [item[0] for item in customer_list if item[0]]

        # 最后更新时间
        last_updated_formula = db.query(func.max(Formulas.updated_at)).scalar()
        last_updated = last_updated_formula.strftime('%Y-%m-%d %H:%M') if last_updated_formula else '无'

        result = {
            'total_formulas': total_formulas,
            'total_ingredients': total_ingredients,
            'product_types': product_types_query,
            'product_type_list': product_type_list,
            'customers': customers_query,
            'customer_list': customer_list,
            'last_updated': last_updated
        }

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"获取配方库统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配方库统计失败: {str(e)}")


@router.get("/reference-formulas")
async def get_reference_formulas(
        skip: int = 0,
        limit: int = 100,
        search: str = None,
        product_type: str = None,
        db: Session = Depends(get_db),
        current_user: Users = Depends(require_login)
):
    """获取配方库列表（支持分页和筛选）"""
    try:
        # 构建查询
        query = db.query(Formulas)

        # 搜索过滤
        if search:
            query = query.filter(Formulas.formula_name.contains(search))

        # 产品类型过滤
        if product_type:
            query = query.filter(Formulas.product_type == product_type)

        # 排序
        query = query.order_by(Formulas.updated_at.desc())

        # 分页
        formulas = query.offset(skip).limit(limit).all()
        result = []

        for formula in formulas:
            ingredients_count = db.query(FormulaIngredients).filter(
                FormulaIngredients.formula_id == formula.id
            ).count()

            # 获取上传者信息
            uploader_name = "未知用户"
            if formula.user_id:
                uploader = db.query(Users).filter(Users.id == formula.user_id).first()
                if uploader:
                    uploader_name = uploader.username

            # 判断当前用户是否可以编辑此配方
            can_edit = current_user.role == 'admin' or formula.user_id == current_user.id

            result.append({
                "id": formula.id,
                "formula_name": formula.formula_name,
                "product_type": formula.product_type,
                "customer": formula.customer,
                "ingredients_count": ingredients_count,
                "updated_at": formula.updated_at.isoformat() if formula.updated_at else None,
                "uploader": uploader_name,
                "user_id": formula.user_id,
                "can_edit": can_edit
            })

        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取配方库列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配方库失败: {str(e)}")


@router.get("/reference-formulas/{formula_id}")
async def get_reference_formula_detail(formula_id: int, db: Session = Depends(get_db)):
    """获取配方库详细信息"""
    try:
        logger.info(f"获取参考配方详情: ID={formula_id}")
        
        formula = db.query(Formulas).filter(Formulas.id == formula_id).first()
        if not formula:
            logger.warning(f"参考配方不存在: ID={formula_id}")
            raise HTTPException(status_code=404, detail="配方不存在")

        logger.info(f"找到参考配方: {formula.formula_name}")

        ingredients = db.query(FormulaIngredients).filter(
            FormulaIngredients.formula_id == formula_id
        ).order_by(FormulaIngredients.ingredient_id, FormulaIngredients.ingredient_sequence).all()
        
        logger.info(f"找到 {len(ingredients)} 个成分记录")

        # 获取配方结构 - 增加错误处理
        try:
            structure = DualFormulaLibraryHandler.get_formula_structure(
                formula_id, db, 'reference'
            )
            logger.info(f"配方结构获取成功")
        except Exception as e:
            logger.error(f"获取配方结构失败: {e}")
            # 如果获取结构失败，使用空结构
            structure = {
                'formula_id': formula_id,
                'table_type': 'reference',
                'ingredients': [],
                'compound_ingredients': [],
                'single_ingredients': []
            }

        # 安全处理成分数据
        processed_ingredients = []
        for ing in ingredients:
            try:
                ingredient_data = {
                    "id": ing.id,
                    "ingredient_id": ing.ingredient_id or 0,
                    "ingredient_sequence": ing.ingredient_sequence or 1,
                    "standard_chinese_name": ing.standard_chinese_name or '',
                    "inci_name": ing.inci_name or '',
                    "ingredient_content": safe_float(ing.ingredient_content),
                    "component_content": safe_float(ing.component_content),
                    "actual_component_content": safe_float(ing.actual_component_content),
                    "purpose": ing.purpose or "其他",
                    "category": ing.purpose or "其他"
                }
                processed_ingredients.append(ingredient_data)
            except Exception as e:
                logger.error(f"处理成分数据失败 (ingredient_id={ing.id}): {e}")
                continue

        result = {
            "id": formula.id,
            "formula_name": formula.formula_name or '',
            "product_type": formula.product_type or '未分类',
            "customer": formula.customer or '',
            "updated_at": formula.updated_at.isoformat() if formula.updated_at else None,
            "ingredients": processed_ingredients,
            "structure": structure
        }

        logger.info(f"参考配方详情获取成功: {result['formula_name']}, 成分数: {len(processed_ingredients)}")
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"获取配方详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取配方详情失败: {str(e)}")


@router.delete("/reference-formulas/{formula_id}")
async def delete_reference_formula(formula_id: int, db: Session = Depends(get_db),
                                   current_user: Users = Depends(require_login)):
    """删除参考配方"""
    try:
        # 查找配方
        formula = db.query(Formulas).filter(Formulas.id == formula_id).first()
        if not formula:
            raise HTTPException(status_code=404, detail="配方不存在")

        # 权限检查：只有管理员或配方上传者可以删除
        if current_user.role != 'admin' and formula.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权删除此配方")

        formula_name = formula.formula_name

        # 1. 删除相关的匹配记录（避免外键约束错误）
        match_records_count = db.query(FormulaMatchRecord).filter(
            FormulaMatchRecord.target_formula_id == formula_id
        ).count()

        if match_records_count > 0:
            db.query(FormulaMatchRecord).filter(
                FormulaMatchRecord.target_formula_id == formula_id
            ).delete()
            logger.info(f"删除了 {match_records_count} 条相关匹配记录")

        # 2. 删除关联的成分（由于外键约束，会自动级联删除）
        ingredients_count = db.query(FormulaIngredients).filter(
            FormulaIngredients.formula_id == formula_id
        ).count()

        # 3. 删除配方
        db.delete(formula)
        db.commit()

        result = {
            "success": True,
            "message": f"配方 '{formula_name}' 及其 {ingredients_count} 个成分已删除",
            "deleted_match_records": match_records_count
        }

        logger.info(f"成功删除配方: {formula_name} (ID: {formula_id})")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"删除参考配方失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除参考配方失败: {str(e)}")


@router.put("/reference-formulas/{formula_id}")
async def edit_reference_formula(
        formula_id: int,
        formula_name: str = Form(...),
        product_type: str = Form("未分类"),
        customer: str = Form(""),
        file: UploadFile = File(None),
        db: Session = Depends(get_db),
        current_user: Users = Depends(require_login)
):
    """编辑参考配方"""
    try:
        # 查找配方
        formula = db.query(Formulas).filter(Formulas.id == formula_id).first()
        if not formula:
            raise HTTPException(status_code=404, detail="配方不存在")

        # 权限检查：只有管理员或配方上传者可以编辑
        if current_user.role != 'admin' and formula.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权编辑此配方")

        old_name = formula.formula_name

        # 同名校验：如果配方名称有变化，检查是否与其他配方重名
        if formula_name != old_name:
            existing_formula = db.query(Formulas).filter(
                Formulas.formula_name == formula_name,
                Formulas.id != formula_id  # 排除当前配方自身
            ).first()
            if existing_formula:
                raise HTTPException(
                    status_code=400,
                    detail=f"参考配方库中已存在名为 '{formula_name}' 的配方，请使用不同的名称"
                )

        # 更新基本信息
        formula.formula_name = formula_name
        formula.product_type = product_type or "未分类"
        formula.customer = customer
        formula.updated_at = datetime.now()

        # 如果上传了新文件，则重新解析成分
        if file and file.filename:
            logger.info(f"重新解析配方文件: {file.filename}")

            # 创建临时文件
            file_extension = os.path.splitext(file.filename)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_path = tmp_file.name
                content = await file.read()
                tmp_file.write(content)

            try:
                # 解析新文件
                parser = FormulaParser()
                parsed_result = parser.parse_file(tmp_path)

                # 检查是否有成分数据
                ingredients_data = parsed_result.get('ingredients', [])
                if not ingredients_data:
                    raise HTTPException(status_code=400, detail="文件中没有找到有效的成分数据")

                # 删除原有成分
                db.query(FormulaIngredients).filter(FormulaIngredients.formula_id == formula_id).delete()

                # 添加新成分 - 使用与添加配方相同的逻辑
                ingredients_created = 0
                parsed_ingredients = parsed_result['ingredients']

                # 按序号分组，检测复配
                ingredient_groups = {}
                for ingredient in parsed_ingredients:
                    seq = ingredient['sequence']
                    if seq not in ingredient_groups:
                        ingredient_groups[seq] = []
                    ingredient_groups[seq].append(ingredient)

                # 处理每个序号组
                for seq, group in ingredient_groups.items():
                    if len(group) == 1:
                        # 单一成分
                        ing = group[0]
                        # 尝试匹配原料目录
                        catalog_match = db.query(IngredientCatalog).filter(
                            IngredientCatalog.chinese_name == ing['chinese_name']
                        ).first()

                        # 使用Excel文件中的原始使用目的字段
                        purpose = ing.get('purpose', '').strip() or '未填写'

                        ingredient = FormulaIngredients(
                            formula_id=formula_id,
                            ingredient_id=seq,
                            ingredient_sequence=1,
                            standard_chinese_name=ing['chinese_name'],
                            inci_name=ing['inci_name'] or None,
                            ingredient_content=ing['percentage'],
                            catalog_id=catalog_match.id if catalog_match else None,
                            component_content=ing.get('ingredient_percentage', 100.0),
                            actual_component_content=ing.get('actual_percentage', ing['percentage']),
                            purpose=purpose
                        )
                        db.add(ingredient)
                        ingredients_created += 1
                    else:
                        # 复配成分
                        for sub_seq, ing in enumerate(group, 1):
                            # 尝试匹配原料目录
                            catalog_match = db.query(IngredientCatalog).filter(
                                IngredientCatalog.chinese_name == ing['chinese_name']
                            ).first()

                            # 使用Excel文件中的原始使用目的字段
                            purpose = ing.get('purpose', '').strip() or '未填写'

                            # 创建复配成分记录
                            ingredient = FormulaIngredients(
                                formula_id=formula_id,
                                ingredient_id=seq,  # 相同的配料ID表示复配
                                ingredient_sequence=sub_seq,  # 不同的序号表示复配中的不同成分
                                standard_chinese_name=ing['chinese_name'],
                                inci_name=ing['inci_name'] or None,
                                ingredient_content=ing['percentage'],  # 在复配中的比例
                                catalog_id=catalog_match.id if catalog_match else None,
                                component_content=ing.get('ingredient_percentage', 100.0),
                                actual_component_content=ing.get('actual_percentage', ing['percentage']),
                                purpose=purpose
                            )
                            db.add(ingredient)
                            ingredients_created += 1

                logger.info(f"更新了 {ingredients_created} 个成分")

            finally:
                # 清理临时文件
                os.unlink(tmp_path)

        # 提交更改
        db.commit()

        result = {
            "success": True,
            "message": f"配方 '{old_name}' 已更新为 '{formula_name}'",
            "formula_id": formula_id,
            "updated_file": bool(file and file.filename)
        }

        logger.info(f"成功编辑配方: {old_name} -> {formula_name} (ID: {formula_id})")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"编辑参考配方失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"编辑参考配方失败: {str(e)}")
