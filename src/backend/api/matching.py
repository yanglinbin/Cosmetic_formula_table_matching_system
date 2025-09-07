#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配方匹配和上传API路由
"""

import os
import json
import tempfile
import shutil
import logging
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.backend.dependencies import get_db, require_login, get_matching_engine
from src.backend.sql.mysql_models import (
    Formulas, FormulaIngredients, FormulasToBeMatched, FormulaIngredientsToBeMatched,
    IngredientCatalog, FormulaMatchRecord, Users, DualFormulaLibraryHandler
)
from src.backend.formula_parser import FormulaParser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["配方匹配"])


class BatchDeleteRequest(BaseModel):
    formula_ids: List[int]


@router.get("/to-match-formulas")
async def get_to_match_formulas(db: Session = Depends(get_db), current_user: Users = Depends(require_login)):
    """获取待匹配配方列表"""
    try:
        # 根据用户角色过滤数据
        if current_user.role == 'admin':
            # 管理员可以看到所有配方
            formulas = db.query(FormulasToBeMatched).order_by(FormulasToBeMatched.updated_at.desc()).all()
        else:
            # 普通用户只能看到自己上传的配方
            formulas = db.query(FormulasToBeMatched).filter(
                FormulasToBeMatched.user_id == current_user.id
            ).order_by(FormulasToBeMatched.updated_at.desc()).all()
        result = []
        for formula in formulas:
            ingredients_count = db.query(FormulaIngredientsToBeMatched).filter(
                FormulaIngredientsToBeMatched.formula_id == formula.id
            ).count()

            # 获取上传者信息
            uploader_name = "未知用户"
            if formula.user_id:
                uploader = db.query(Users).filter(Users.id == formula.user_id).first()
                if uploader:
                    uploader_name = uploader.username

            result.append({
                "id": formula.id,
                "formula_name": formula.formula_name,
                "product_type": formula.product_type,
                "customer": formula.customer,
                "ingredients_count": ingredients_count,
                "updated_at": formula.updated_at.isoformat() if formula.updated_at else None,
                "uploader": uploader_name,
                "user_id": formula.user_id
            })

        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取待匹配配方列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取待匹配配方失败: {str(e)}")


@router.delete("/to-match-formulas/batch")
async def batch_delete_to_match_formulas(request: BatchDeleteRequest, db: Session = Depends(get_db)):
    """批量删除待匹配配方"""
    try:
        formula_ids = request.formula_ids
        if not formula_ids:
            raise HTTPException(status_code=400, detail="未提供要删除的配方ID列表")

        deleted_formulas = []
        total_ingredients_deleted = 0
        total_match_records_deleted = 0

        for formula_id in formula_ids:
            # 查找配方
            formula = db.query(FormulasToBeMatched).filter(FormulasToBeMatched.id == formula_id).first()
            if not formula:
                logger.warning(f"配方ID {formula_id} 不存在，跳过")
                continue

            formula_name = formula.formula_name

            # 1. 删除相关的匹配记录
            match_records_count = db.query(FormulaMatchRecord).filter(
                FormulaMatchRecord.source_formula_id == formula_id
            ).count()

            if match_records_count > 0:
                db.query(FormulaMatchRecord).filter(
                    FormulaMatchRecord.source_formula_id == formula_id
                ).delete()
                total_match_records_deleted += match_records_count

            # 2. 统计关联成分数量
            ingredients_count = db.query(FormulaIngredientsToBeMatched).filter(
                FormulaIngredientsToBeMatched.formula_id == formula_id
            ).count()
            total_ingredients_deleted += ingredients_count

            # 3. 删除配方（成分会通过外键级联删除）
            db.delete(formula)
            deleted_formulas.append({
                "id": formula_id,
                "name": formula_name,
                "ingredients_count": ingredients_count,
                "match_records_count": match_records_count
            })

        # 提交所有删除操作
        db.commit()

        result = {
            "success": True,
            "message": f"批量删除完成，共删除 {len(deleted_formulas)} 个配方",
            "deleted_count": len(deleted_formulas),
            "deleted_ingredients_count": total_ingredients_deleted,
            "deleted_match_records_count": total_match_records_deleted,
            "deleted_formulas": deleted_formulas
        }

        logger.info(
            f"批量删除待匹配配方成功: 删除了 {len(deleted_formulas)} 个配方，{total_ingredients_deleted} 个成分，{total_match_records_deleted} 条匹配记录")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除待匹配配方失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量删除待匹配配方失败: {str(e)}")


@router.delete("/to-match-formulas/{formula_id}")
async def delete_to_match_formula(formula_id: int, db: Session = Depends(get_db)):
    """删除待匹配配方"""
    try:
        # 查找配方
        formula = db.query(FormulasToBeMatched).filter(FormulasToBeMatched.id == formula_id).first()
        if not formula:
            raise HTTPException(status_code=404, detail="待匹配配方不存在")

        formula_name = formula.formula_name

        # 1. 删除相关的匹配记录（避免外键约束错误）
        match_records_count = db.query(FormulaMatchRecord).filter(
            FormulaMatchRecord.source_formula_id == formula_id
        ).count()

        if match_records_count > 0:
            db.query(FormulaMatchRecord).filter(
                FormulaMatchRecord.source_formula_id == formula_id
            ).delete()
            logger.info(f"删除了 {match_records_count} 条相关匹配记录")

        # 2. 删除关联的成分（由于外键约束，会自动级联删除）
        ingredients_count = db.query(FormulaIngredientsToBeMatched).filter(
            FormulaIngredientsToBeMatched.formula_id == formula_id
        ).count()

        # 3. 删除配方
        db.delete(formula)
        db.commit()

        result = {
            "success": True,
            "message": f"待匹配配方 '{formula_name}' 及其 {ingredients_count} 个成分已删除",
            "deleted_match_records": match_records_count
        }

        logger.info(f"成功删除待匹配配方: {formula_name} (ID: {formula_id})")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"删除待匹配配方失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除待匹配配方失败: {str(e)}")


@router.post("/upload-formula")
async def upload_formula_unified(
        file: UploadFile = File(...),
        formula_name: str = Form(...),
        product_type: str = Form("未分类"),
        customer: str = Form(""),
        target_library: str = Form("to_match"),  # "reference" 或 "to_match"
        db: Session = Depends(get_db),
        current_user: Users = Depends(require_login)
):
    """统一上传配方API - 支持参考库和待匹配库"""
    try:
        # 验证目标库参数
        if target_library not in ['reference', 'to_match']:
            raise HTTPException(status_code=400, detail="target_library必须是'reference'或'to_match'")

        # 验证文件格式（大小写不敏感）
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持Excel格式文件(.xlsx, .xls)")

        # 保存临时文件
        file_extension = '.xlsx' if file.filename.lower().endswith('.xlsx') else '.xls'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            # 使用FormulaParser解析Excel文件
            parser = FormulaParser()
            parsed_result = parser.parse_file(tmp_path)

            logger.info(
                f"解析Excel文件: {file.filename}, 成分数: {parsed_result['total_ingredients']}, 目标库: {target_library}")

            # 使用用户输入的配方名称，如果没有则使用解析出的名称
            final_formula_name = formula_name or parsed_result['name']

            # 同名校验：检查目标库中是否已存在同名配方
            if target_library == 'reference':
                existing_formula = db.query(Formulas).filter(
                    Formulas.formula_name == final_formula_name
                ).first()
                if existing_formula:
                    raise HTTPException(
                        status_code=400,
                        detail=f"参考配方库中已存在名为 '{final_formula_name}' 的配方，请使用不同的名称"
                    )
            else:
                existing_formula = db.query(FormulasToBeMatched).filter(
                    FormulasToBeMatched.formula_name == final_formula_name
                ).first()
                if existing_formula:
                    raise HTTPException(
                        status_code=400,
                        detail=f"待匹配配方库中已存在名为 '{final_formula_name}' 的配方，请使用不同的名称"
                    )

            # 根据目标库选择不同的模型和处理逻辑
            if target_library == 'reference':
                # 创建参考配方记录
                new_formula = Formulas(
                    formula_name=final_formula_name,
                    product_type=product_type,
                    customer=customer,
                    user_id=current_user.id
                )
                formula_model = Formulas
                ingredient_model = FormulaIngredients
                library_name = "参考配方库"
            else:
                # 创建待匹配配方记录
                new_formula = FormulasToBeMatched(
                    formula_name=final_formula_name,
                    product_type=product_type,
                    customer=customer,
                    user_id=current_user.id
                )
                formula_model = FormulasToBeMatched
                ingredient_model = FormulaIngredientsToBeMatched
                library_name = "待匹配配方库"

            db.add(new_formula)
            db.flush()  # 获取ID

            # 解析配方成分
            ingredients_created = 0
            parsed_ingredients = parsed_result['ingredients']

            # 按序号分组，检测复配
            ingredient_groups = {}
            for ingredient in parsed_ingredients:
                seq = ingredient['sequence']
                if seq not in ingredient_groups:
                    ingredient_groups[seq] = []
                ingredient_groups[seq].append(ingredient)

            # 处理每个成分组
            for seq, group in ingredient_groups.items():
                if len(group) == 1:
                    # 单配成分
                    ing = group[0]

                    # 尝试匹配原料目录
                    catalog_match = db.query(IngredientCatalog).filter(
                        IngredientCatalog.chinese_name == ing['chinese_name']
                    ).first()

                    # 使用Excel文件中的原始使用目的字段
                    purpose = ing.get('purpose', '').strip() or '未填写'

                    # 创建成分记录
                    ingredient = ingredient_model(
                        formula_id=new_formula.id,
                        ingredient_id=seq,
                        ingredient_sequence=1,  # 单配序号为1
                        standard_chinese_name=ing['chinese_name'],
                        inci_name=ing['inci_name'] or None,
                        ingredient_content=ing['percentage'],
                        catalog_id=catalog_match.id if catalog_match else None,
                        component_content=ing.get('ingredient_percentage', 100.0),
                        actual_component_content=ing.get('actual_percentage', ing['percentage']),
                        purpose=purpose  # 添加使用目的
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
                        ingredient = ingredient_model(
                            formula_id=new_formula.id,
                            ingredient_id=seq,  # 相同的配料ID表示复配
                            ingredient_sequence=sub_seq,  # 不同的序号表示复配中的不同成分
                            standard_chinese_name=ing['chinese_name'],
                            inci_name=ing['inci_name'] or None,
                            ingredient_content=ing['percentage'],  # 在复配中的比例
                            catalog_id=catalog_match.id if catalog_match else None,
                            component_content=ing.get('ingredient_percentage', 100.0),
                            actual_component_content=ing.get('actual_percentage', ing['percentage']),
                            purpose=purpose  # 添加使用目的
                        )
                        db.add(ingredient)
                        ingredients_created += 1

            db.commit()

            # 构建返回结果
            validation = parsed_result.get('validation', {})
            result = {
                "success": True,
                "formula_id": new_formula.id,
                "formula_name": final_formula_name,
                "ingredients_count": ingredients_created,
                "total_percentage": validation.get('total_percentage', 0),
                "compound_count": validation.get('compound_count', 0),
                "validation_warnings": validation.get('warnings', []),
                "validation_errors": validation.get('errors', []),
                "is_valid": validation.get('is_valid', True),
                "target_library": target_library,
                "library_name": library_name,
                "message": f"成功上传配方到{library_name}，解析了{ingredients_created}个成分"
            }

            return JSONResponse(content=result)

        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        db.rollback()
        logger.error(f"上传配方失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传配方失败: {str(e)}")


@router.post("/match-formula/{formula_id}")
async def match_formula(
        formula_id: int,
        strict_mode: bool = False,
        db: Session = Depends(get_db)
):
    """执行配方匹配"""
    try:
        # 检查待匹配配方是否存在
        source_formula = db.query(FormulasToBeMatched).filter(
            FormulasToBeMatched.id == formula_id
        ).first()

        if not source_formula:
            raise HTTPException(status_code=404, detail="待匹配配方不存在")

        logger.info(f"开始匹配配方: {source_formula.formula_name} (ID: {formula_id}), 严格模式: {strict_mode}")

        # 获取匹配引擎
        matching_engine = get_matching_engine(db)

        # 执行匹配，传递严格范围匹配参数
        match_results = matching_engine.match_formula_against_library(
            source_formula_id=formula_id,
            session=db,
            strict_mode=strict_mode
        )

        logger.info(f"匹配完成，找到 {len(match_results)} 个结果")

        # 保存匹配记录
        for result in match_results:
            match_record = FormulaMatchRecord(
                source_formula_id=formula_id,
                target_formula_id=result.target_formula_id,
                similarity_score=result.similarity_score,
                composition_similarity=result.composition_similarity,
                proportion_similarity=result.proportion_similarity,
                common_ingredients_count=result.common_ingredients_count,
                total_ingredients_count=result.total_ingredients_count,
                match_details=json.dumps({
                    "composition_similarity": result.composition_similarity,
                    "proportion_similarity": result.proportion_similarity,
                    "category_similarities": result.category_similarities,
                    "common_ingredients": result.common_ingredients,
                    "common_ingredients_count": result.common_ingredients_count,
                    "total_ingredients_count": result.total_ingredients_count,
                    "match_details": result.match_details
                }, ensure_ascii=False),
                algorithm_version="dual_library_v1.0"
            )
            db.add(match_record)

        db.commit()

        # 构建返回结果
        formatted_results = []
        for result in match_results:
            formatted_results.append({
                "target_formula_id": result.target_formula_id,
                "target_formula_name": result.target_formula_name,
                "similarity_score": round(result.similarity_score, 10),
                "composition_similarity": round(result.composition_similarity, 10),
                "proportion_similarity": round(result.proportion_similarity, 10),
                "common_ingredients": result.common_ingredients,
                "common_ingredients_count": result.common_ingredients_count,
                "total_ingredients_count": result.total_ingredients_count,
                "category_similarities": {k: round(v, 10) for k, v in result.category_similarities.items()},
                "match_details": result.match_details
            })

        # 获取匹配统计
        statistics = matching_engine.get_matching_statistics(match_results)

        return JSONResponse(content={
            "success": True,
            "source_formula_id": formula_id,
            "source_formula_name": source_formula.formula_name,
            "match_results": formatted_results,
            "total_matches": len(match_results),
            "statistics": statistics,
            "algorithm": "dual_library_v1.0",
            "parameters": {
                "composition_weight": matching_engine.parameters.composition_weight,
                "proportion_weight": matching_engine.parameters.proportion_weight,
                "category_weights": matching_engine.parameters.category_weights,
                "max_results": matching_engine.parameters.max_results
            }
        })

    except Exception as e:
        logger.error(f"配方匹配失败: {e}")
        raise HTTPException(status_code=500, detail=f"配方匹配失败: {str(e)}")


@router.get("/formula-detail/{formula_id}")
async def get_formula_detail(
        formula_id: int,
        formula_type: str = "reference",
        db: Session = Depends(get_db)
):
    """获取配方详细信息 - 用于详情查看"""
    try:
        logger.info(f"获取配方详情: ID={formula_id}, type={formula_type}")
        
        # 根据类型选择表
        if formula_type == "reference":
            FormulaModel = Formulas
            IngredientModel = FormulaIngredients
        else:  # to_be_matched
            FormulaModel = FormulasToBeMatched
            IngredientModel = FormulaIngredientsToBeMatched

        # 获取配方基本信息
        formula = db.query(FormulaModel).filter(FormulaModel.id == formula_id).first()
        if not formula:
            logger.warning(f"配方不存在: ID={formula_id}, type={formula_type}")
            raise HTTPException(status_code=404, detail="配方不存在")
        
        logger.info(f"找到配方: {formula.formula_name}")

        # 获取配方结构 - 增加错误处理
        try:
            formula_structure = DualFormulaLibraryHandler.get_formula_structure(
                formula_id, db, formula_type
            )
            logger.info(f"配方结构获取成功，包含 {len(formula_structure.get('ingredients', []))} 个成分")
        except Exception as e:
            logger.error(f"获取配方结构失败: {e}")
            # 如果获取结构失败，使用空结构
            formula_structure = {
                'formula_id': formula_id,
                'table_type': formula_type,
                'ingredients': [],
                'compound_ingredients': [],
                'single_ingredients': []
            }

        # 获取成分详细信息
        ingredients = db.query(IngredientModel).filter(
            IngredientModel.formula_id == formula_id
        ).order_by(IngredientModel.ingredient_id, IngredientModel.ingredient_sequence).all()
        
        logger.info(f"找到 {len(ingredients)} 个成分记录")

        # 构建详细的成分列表
        ingredients_data = []
        for ingredient in ingredients:
            try:
                # 尝试获取原料目录信息
                catalog_info = None
                if ingredient.catalog_id:
                    try:
                        catalog = db.query(IngredientCatalog).filter(
                            IngredientCatalog.id == ingredient.catalog_id
                        ).first()
                        if catalog:
                            catalog_info = {
                                "id": catalog.id,
                                "chinese_name": catalog.chinese_name or '',
                                "inci_name": catalog.inci_name or ''
                            }
                    except Exception as e:
                        logger.warning(f"获取原料目录信息失败: {e}")

                # 获取使用目的（优先使用数据库中的purpose字段）
                purpose = ingredient.purpose or "未填写"

                # 安全地转换数值字段 - 保持10位小数精度
                ingredient_content = round(float(ingredient.ingredient_content or 0), 10)
                component_content = round(float(ingredient.component_content or 0), 10)
                actual_component_content = round(float(ingredient.actual_component_content or 0), 10)

                ingredients_data.append({
                    "id": ingredient.id,
                    "ingredient_id": ingredient.ingredient_id or 0,
                    "ingredient_sequence": ingredient.ingredient_sequence or 1,
                    "standard_chinese_name": ingredient.standard_chinese_name or '',
                    "inci_name": ingredient.inci_name or '',
                    "ingredient_content": ingredient_content,
                    "component_content": component_content,
                    "actual_component_content": actual_component_content,
                    "catalog_id": ingredient.catalog_id,
                    "catalog_info": catalog_info,
                    "category": purpose,  # 使用purpose作为category
                    "purpose": purpose  # 同时也返回purpose字段
                })
            except Exception as e:
                logger.error(f"处理成分数据失败 (ingredient_id={ingredient.id}): {e}")
                continue

        # 统计信息 - 改进错误处理，保持10位小数精度
        try:
            total_content = round(sum([float(ing.get('ingredient_content', 0)) for ing in ingredients_data]), 10)
        except Exception as e:
            logger.error(f"计算总含量失败: {e}")
            total_content = 0
            
        categories_count = {}
        for ing_data in ingredients_data:
            category = ing_data.get('category', '未填写')
            categories_count[category] = categories_count.get(category, 0) + 1

        result = {
            "id": formula.id,
            "formula_name": formula.formula_name or '',
            "product_type": formula.product_type or '未分类',
            "customer": formula.customer or '',
            "formula_type": formula_type,
            "updated_at": formula.updated_at.isoformat() if formula.updated_at else None,
            "ingredients": ingredients_data,
            "structure": formula_structure,
            "statistics": {
                "ingredients_count": len(ingredients_data),
                "total_content": total_content,  # 已在计算时保持10位精度
                "categories_count": categories_count,
                "single_ingredients_count": len(formula_structure.get('single_ingredients', [])),
                "compound_ingredients_count": len(formula_structure.get('compound_ingredients', []))
            }
        }
        
        logger.info(f"配方详情获取成功: {result['formula_name']}, 成分数: {len(ingredients_data)}")
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配方详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取配方详情失败: {str(e)}")


@router.get("/customers")
async def get_customers(db: Session = Depends(get_db), current_user: Users = Depends(require_login)):
    """获取客户列表"""
    try:
        # 从两个配方表中获取所有唯一的客户名称
        reference_customers = db.query(Formulas.customer).filter(
            Formulas.customer.isnot(None),
            Formulas.customer != ""
        ).distinct().all()
        
        to_match_customers = db.query(FormulasToBeMatched.customer).filter(
            FormulasToBeMatched.customer.isnot(None),
            FormulasToBeMatched.customer != ""
        ).distinct().all()
        
        # 合并并去重
        all_customers = set()
        for customer_tuple in reference_customers:
            if customer_tuple[0] and customer_tuple[0].strip():
                all_customers.add(customer_tuple[0].strip())
        
        for customer_tuple in to_match_customers:
            if customer_tuple[0] and customer_tuple[0].strip():
                all_customers.add(customer_tuple[0].strip())
        
        # 按字母排序
        customer_list = sorted(list(all_customers))
        
        return JSONResponse(content={
            "success": True,
            "customers": customer_list
        })
    
    except Exception as e:
        logger.error(f"获取客户列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客户列表失败: {str(e)}")


@router.post("/formula-comparison")
async def compare_formulas_api(
        request: dict,
        db: Session = Depends(get_db)
):
    """配方对比分析"""
    try:
        source_id = request.get('source_formula_id')
        target_id = request.get('target_formula_id')

        if not source_id or not target_id:
            raise HTTPException(status_code=400, detail="缺少配方ID参数")

        # 获取源配方（待匹配）
        source_formula = db.query(FormulasToBeMatched).filter(
            FormulasToBeMatched.id == source_id
        ).first()
        if not source_formula:
            raise HTTPException(status_code=404, detail="源配方不存在")

        # 获取目标配方（参考配方）
        target_formula = db.query(Formulas).filter(
            Formulas.id == target_id
        ).first()
        if not target_formula:
            raise HTTPException(status_code=404, detail="目标配方不存在")

        # 获取配方结构
        source_structure = DualFormulaLibraryHandler.get_formula_structure(
            source_id, db, 'to_be_matched'
        )
        target_structure = DualFormulaLibraryHandler.get_formula_structure(
            target_id, db, 'reference'
        )

        # 使用匹配引擎进行详细分析
        matching_engine = get_matching_engine(db)

        # 执行单对配方的详细匹配分析
        match_result = matching_engine._match_single_pair(
            source_formula, source_structure, target_id, db
        )

        if not match_result:
            raise HTTPException(status_code=500, detail="匹配分析失败")

        # 提取成分列表进行详细对比
        source_ingredients_list = matching_engine._extract_ingredients_list(source_structure)
        target_ingredients_list = matching_engine._extract_ingredients_list(target_structure)

        # 分析共同成分和差异成分
        source_names = set()
        target_names = set()
        source_compounds_detail = {}  # 存储复配详细信息
        target_compounds_detail = {}

        # 保存成分的详细信息，包括分类
        source_ingredients_detail = {}  # 成分名称 -> 成分信息
        target_ingredients_detail = {}

        for ing in source_ingredients_list:
            if ing.get('type') == 'single':
                name = ing['chinese_name']
                source_names.add(name)
                source_ingredients_detail[name] = {
                    'type': 'single',
                    'category': ing.get('purpose', '其他')  # 使用purpose字段
                }
            elif ing.get('type') == 'compound':
                compound_name = ing['chinese_name']
                source_names.add(compound_name)
                source_ingredients_detail[compound_name] = {
                    'type': 'compound',
                    'category': ing.get('purpose', '其他')  # 使用purpose字段
                }
                # 保存复配详细信息 - 从components_detail中提取
                components = []
                components_detail = ing.get('components_detail', [])
                for comp in components_detail:
                    components.append(comp.get('chinese_name', ''))
                source_compounds_detail[compound_name] = components

        for ing in target_ingredients_list:
            if ing.get('type') == 'single':
                name = ing['chinese_name']
                target_names.add(name)
                target_ingredients_detail[name] = {
                    'type': 'single',
                    'category': ing.get('purpose', '其他')  # 使用purpose字段
                }
            elif ing.get('type') == 'compound':
                compound_name = ing['chinese_name']
                target_names.add(compound_name)
                target_ingredients_detail[compound_name] = {
                    'type': 'compound',
                    'category': ing.get('purpose', '其他')  # 使用purpose字段
                }
                # 保存复配详细信息 - 从components_detail中提取
                components = []
                components_detail = ing.get('components_detail', [])
                for comp in components_detail:
                    components.append(comp.get('chinese_name', ''))
                target_compounds_detail[compound_name] = components

        # 自定义排序函数：按分类优先级排序，每个分类内单配在前复配在后
        def custom_ingredient_sort(ingredients_list, ingredients_detail_dict):
            # 分类优先级顺序
            category_priority = {
                '防腐剂': 1,
                '乳化剂': 2,
                '增稠剂': 3,
                '抗氧化剂': 4,
                '表面活性剂': 5,
                '其他': 6
            }

            # purpose字段到分类的映射关系
            purpose_to_category_map = {
                # 防腐剂相关
                '防腐剂': '防腐剂',

                # 乳化剂相关
                '乳化剂': '乳化剂',

                # 增稠剂相关
                '增稠剂': '增稠剂',

                # 抗氧化剂相关
                '抗氧化剂': '抗氧化剂',

                # 表面活性剂相关
                '表面活性剂': '表面活性剂',

            }

            def map_purpose_to_category(purpose):
                """将purpose字段映射到标准分类"""
                if not purpose:
                    return '其他'

                purpose_lower = purpose.lower().strip()

                # 直接匹配
                for key, category in purpose_to_category_map.items():
                    if key in purpose_lower:
                        return category

                # 如果没有匹配，返回其他
                return '其他'

            def get_sort_key(ingredient_name):
                detail = ingredients_detail_dict.get(ingredient_name, {'type': 'single', 'category': '其他'})
                raw_category = detail['category']
                ingredient_type = detail['type']

                # 将purpose映射到标准分类
                mapped_category = map_purpose_to_category(raw_category)

                # 返回排序键：(分类优先级, 类型优先级, 成分名称)
                # 类型优先级：single=0, compound=1（单配在前）
                type_priority = 0 if ingredient_type == 'single' else 1

                return (category_priority[mapped_category], type_priority, ingredient_name)

            # 按排序键排序
            return sorted(ingredients_list, key=get_sort_key)

        # 合并成分详细信息字典
        all_ingredients_detail = {**source_ingredients_detail, **target_ingredients_detail}

        # 生成排序后的成分列表
        common_ingredients = custom_ingredient_sort(list(source_names & target_names), all_ingredients_detail)
        source_only = custom_ingredient_sort(list(source_names - target_names), all_ingredients_detail)
        target_only = custom_ingredient_sort(list(target_names - source_names), all_ingredients_detail)

        # 生成分类分组数据
        def group_ingredients_by_category(ingredients_list, ingredients_detail_dict, map_purpose_func):
            """将成分按分类分组"""
            category_groups = {
                '防腐剂': [],
                '乳化剂': [],
                '增稠剂': [],
                '抗氧化剂': [],
                '表面活性剂': [],
                '其他': []
            }

            for ingredient in ingredients_list:
                detail = ingredients_detail_dict.get(ingredient, {'type': 'single', 'category': '其他'})
                raw_category = detail.get('category', '其他')
                mapped_category = map_purpose_func(raw_category)

                category_groups[mapped_category].append({
                    'name': ingredient,
                    'type': detail.get('type', 'single'),
                    'raw_category': raw_category
                })

            # 移除空的分类组
            return {k: v for k, v in category_groups.items() if v}

        # purpose字段到分类的映射关系（复用排序函数中的逻辑）
        def map_purpose_to_category_for_grouping(purpose):
            """将purpose字段映射到标准分类"""
            if not purpose:
                return '其他'

            purpose_lower = purpose.lower().strip()

            # purpose字段到分类的映射关系
            purpose_to_category_map = {
                # 防腐剂相关
                '防腐剂': '防腐剂',

                # 乳化剂相关
                '乳化剂': '乳化剂',

                # 增稠剂相关
                '增稠剂': '增稠剂',

                # 抗氧化剂相关
                '抗氧化剂': '抗氧化剂',

                # 表面活性剂相关
                '表面活性剂': '表面活性剂',

            }

            # 直接匹配
            for key, category in purpose_to_category_map.items():
                if key in purpose_lower:
                    return category

            # 如果没有匹配，返回其他
            return '其他'

        # 为三个成分列表生成分类分组数据
        common_ingredients_grouped = group_ingredients_by_category(common_ingredients, all_ingredients_detail,
                                                                   map_purpose_to_category_for_grouping)
        source_only_grouped = group_ingredients_by_category(source_only, all_ingredients_detail,
                                                            map_purpose_to_category_for_grouping)
        target_only_grouped = group_ingredients_by_category(target_only, all_ingredients_detail,
                                                            map_purpose_to_category_for_grouping)

        # 按分类分析共同成分
        category_analysis = {}
        for category in ["防腐剂", "乳化剂", "增稠剂", "抗氧化剂", "表面活性剂", "其他"]:
            category_analysis[category] = {
                "source_count": 0,
                "target_count": 0,
                "common_count": 0,
                "source_ingredients": [],
                "target_ingredients": [],
                "common_ingredients": []
            }

        # 分类统计（使用原始purpose字段）

        for ing in source_ingredients_list:
            if ing.get('type') == 'single':
                # 直接使用purpose字段作为分类
                category = ing.get('purpose', '未填写').strip() or '未填写'
                if category not in category_analysis:
                    category_analysis[category] = {
                        "source_count": 0, "target_count": 0, "common_count": 0,
                        "source_ingredients": [], "target_ingredients": [], "common_ingredients": []
                    }
                category_analysis[category]["source_count"] += 1
                category_analysis[category]["source_ingredients"].append(ing['chinese_name'])

                if ing['chinese_name'] in common_ingredients:
                    category_analysis[category]["common_count"] += 1
                    category_analysis[category]["common_ingredients"].append(ing['chinese_name'])

        for ing in target_ingredients_list:
            if ing.get('type') == 'single':
                # 直接使用purpose字段作为分类
                category = ing.get('purpose', '未填写').strip() or '未填写'
                if category not in category_analysis:
                    category_analysis[category] = {
                        "source_count": 0, "target_count": 0, "common_count": 0,
                        "source_ingredients": [], "target_ingredients": [], "common_ingredients": []
                    }
                category_analysis[category]["target_count"] += 1
                category_analysis[category]["target_ingredients"].append(ing['chinese_name'])

        # 对分类分析中的成分列表也应用排序逻辑
        for category in category_analysis:
            if category_analysis[category]["source_ingredients"]:
                category_analysis[category]["source_ingredients"] = custom_ingredient_sort(
                    category_analysis[category]["source_ingredients"], all_ingredients_detail
                )
            if category_analysis[category]["target_ingredients"]:
                category_analysis[category]["target_ingredients"] = custom_ingredient_sort(
                    category_analysis[category]["target_ingredients"], all_ingredients_detail
                )
            if category_analysis[category]["common_ingredients"]:
                category_analysis[category]["common_ingredients"] = custom_ingredient_sort(
                    category_analysis[category]["common_ingredients"], all_ingredients_detail
                )

        # ==================== 新增：原料对比分析 ====================
        
        def extract_actual_components(formula_structure):
            """从配方结构中提取所有实际成分（拆分复配）"""
            actual_components = {}  # {成分名: actual_component_content}
            
            # 处理单配成分
            for ingredient in formula_structure.get('single_ingredients', []):
                name = ingredient.get('chinese_name', '').strip()
                if name:
                    content = float(ingredient.get('actual_content', 0))
                    if name in actual_components:
                        actual_components[name] += content
                    else:
                        actual_components[name] = content
            
            # 处理复配成分 - 拆分为单一原料
            for compound in formula_structure.get('compound_ingredients', []):
                components = compound.get('components', [])
                for component in components:
                    name = component.get('chinese_name', '').strip()
                    if name:
                        content = float(component.get('actual_content', 0))
                        if name in actual_components:
                            actual_components[name] += content
                        else:
                            actual_components[name] = content
            
            return actual_components
        
        # 提取两个配方的实际成分
        source_actual_components = extract_actual_components(source_structure)
        target_actual_components = extract_actual_components(target_structure)
        
        # 找出共有的原料
        common_ingredient_names = set(source_actual_components.keys()) & set(target_actual_components.keys())
        
        # 构建共有原料对比数据
        ingredient_comparison_data = []
        for ingredient_name in sorted(common_ingredient_names):  # 按字母排序
            source_content = source_actual_components[ingredient_name]
            target_content = target_actual_components[ingredient_name]
            
            ingredient_comparison_data.append({
                "name": ingredient_name,
                "source_content": round(source_content, 10),
                "target_content": round(target_content, 10)
            })
        
        # 按含量排序（取两个配方中的较大值作为排序依据）
        ingredient_comparison_data.sort(key=lambda x: max(x['source_content'], x['target_content']), reverse=True)
        
        logger.info(f"原料对比分析完成：共有原料 {len(ingredient_comparison_data)} 个")

        # 构建对比结果
        comparison_result = {
            "source_formula": {
                "id": source_formula.id,
                "name": source_formula.formula_name,
                "type": "待匹配配方",
                "product_type": source_formula.product_type,
                "customer": source_formula.customer,
                "ingredients_count": len(source_ingredients_list)
            },
            "target_formula": {
                "id": target_formula.id,
                "name": target_formula.formula_name,
                "type": "参考配方",
                "product_type": target_formula.product_type,
                "customer": target_formula.customer,
                "ingredients_count": len(target_ingredients_list)
            },
            "similarity_analysis": {
                "total_similarity": round(match_result.similarity_score, 10),
                "composition_similarity": round(match_result.composition_similarity, 10),
                "proportion_similarity": round(match_result.proportion_similarity, 10),
                "category_similarities": {k: round(v, 10) for k, v in match_result.category_similarities.items()}
            },
            "ingredients_analysis": {
                "common_ingredients": common_ingredients,
                "common_count": len(common_ingredients),
                "source_only": source_only,
                "source_only_count": len(source_only),
                "target_only": target_only,
                "target_only_count": len(target_only),
                "total_unique": len(source_names | target_names),
                "source_compounds_detail": source_compounds_detail,
                "target_compounds_detail": target_compounds_detail,
                # 添加分类分组数据
                "common_ingredients_grouped": common_ingredients_grouped,
                "source_only_grouped": source_only_grouped,
                "target_only_grouped": target_only_grouped
            },
            "category_analysis": category_analysis,
            "match_details": match_result.match_details,
            # 新增：原料对比数据
            "ingredient_comparison": {
                "common_ingredients": ingredient_comparison_data,
                "common_count": len(ingredient_comparison_data),
                "source_total_components": len(source_actual_components),
                "target_total_components": len(target_actual_components)
            }
        }

        return JSONResponse(content=comparison_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"配方对比分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"配方对比分析失败: {str(e)}")
