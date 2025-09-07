// 使用共享组件的全局变量
let formulaUploadHandler;

// ==================== 数字格式化工具函数 ====================

/**
 * 智能数字格式化函数
 * 保留最多10位小数，自动截断末尾的0
 * @param {number|string} num - 要格式化的数字
 * @param {number} maxDecimals - 最大小数位数，默认10
 * @returns {string} 格式化后的数字字符串
 */
function formatSmartNumber(num, maxDecimals = 10) {
    if (num == null || num === '' || isNaN(num)) {
        return '0';
    }
    
    const number = parseFloat(num);
    
    // 处理整数情况
    if (Number.isInteger(number)) {
        return number.toString();
    }
    
    // 转换为最大精度的字符串
    let formatted = number.toFixed(maxDecimals);
    
    // 移除末尾的0和小数点
    formatted = formatted.replace(/\.?0+$/, '');
    
    // 如果结果为空，返回'0'
    if (formatted === '' || formatted === '.') {
        return '0';
    }
    
    return formatted;
}

/**
 * 百分比格式化函数
 * @param {number|string} num - 要格式化的数字
 * @param {number} maxDecimals - 最大小数位数，默认10
 * @returns {string} 格式化后的百分比字符串
 */
function formatPercentage(num, maxDecimals = 10) {
    return formatSmartNumber(num, maxDecimals) + '%';
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function () {
    initializeUploadMatchPage();
});

// 初始化上传匹配页面
async function initializeUploadMatchPage() {
    // 使用共享组件初始化上传表单
    formulaUploadHandler = new FormulaUploadHandler();
    await formulaUploadHandler.initializeUploadForm({
        onProductTypeRecognized: (formulaName) => {
            console.log(`产品类型识别成功: ${formulaName}`);
            // 可以在这里添加更多的处理逻辑
        }
    });
    
    // 加载页面特定数据
    loadToMatchFormulas();
}

// 使用共享组件管理产品类型配置
// 移除重复代码，由FormulaUploadHandler处理

// 填充产品大类选择器 - 使用共享组件
// 由FormulaUploadHandler自动处理

// 更新子分类选择器 - 使用共享组件
function updateUploadSubcategories() {
    if (formulaUploadHandler && formulaUploadHandler.productTypeManager) {
        formulaUploadHandler.productTypeManager.updateSubcategories(
            'uploadProductCategory',
            'uploadProductSubcategory',
            'uploadFinalProductType'
        );
    }
}

// 手动识别产品类型
function manualRecognizeProductType() {
    const formulaNameInput = document.getElementById('formulaName');
    const formulaName = formulaNameInput.value.trim();
    
    if (!formulaName) {
        showAlert('warning', '请先输入配方名称');
        return;
    }
    
    if (formulaUploadHandler && formulaUploadHandler.manualRecognizeProductType) {
        const recognized = formulaUploadHandler.manualRecognizeProductType(
            formulaName,
            'uploadProductCategory',
            'uploadProductSubcategory', 
            'uploadFinalProductType'
        );
        
        if (recognized) {
            // 获取识别结果详情以显示更详细的信息
            const recognizeResult = formulaUploadHandler.productTypeRecognizer.recognizeProductType(formulaName);
            const matchMethod = recognizeResult.matchedBy === 'mapping' ? '映射表匹配' : '关键词匹配';
            showAlert('success', `已根据配方名称 "${formulaName}" 自动识别产品类型！<br><small>识别方式：${matchMethod}</small>`);
        } else {
            showAlert('info', `未能从配方名称 "${formulaName}" 中识别出产品类型，请手动选择。<br><small>提示：可以在系统配置中添加产品类型映射</small>`);
        }
    } else {
        showAlert('error', '产品类型识别器未初始化，请刷新页面重试。');
    }
}

// 加载待匹配配方列表
function loadToMatchFormulas() {
    fetch('/api/v1/to-match-formulas')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const list = document.getElementById('formulasList');
            const selectAllContainer = document.getElementById('selectAllContainer');
            const batchActions = document.getElementById('batchActions');

            if (data.length === 0) {
                list.innerHTML = '<p class="text-muted">暂无待匹配配方</p>';
                selectAllContainer.style.display = 'none';
                batchActions.style.display = 'none';
                return;
            }

            // 显示批量操作控件
            selectAllContainer.style.display = 'block';
            batchActions.style.display = 'block';

            let html = '<div class="formulas-list">';
            data.forEach(formula => {
                html += `
                                    <div class="formula-list-item">
                                        <div class="d-flex align-items-center">
                                            <div class="form-check me-3">
                                                <input class="form-check-input formula-checkbox" type="checkbox" 
                                                       value="${formula.id}" onchange="updateBatchControls()">
                                            </div>
                                            <div class="flex-grow-1">
                                                <div class="formula-name">${formula.formula_name}</div>
                                                <div class="formula-info">
                                                    <span class="info-item">
                                                        <i class="fas fa-tag"></i> ${formula.product_type || '未分类'}
                                                    </span>
                                                    <span class="info-item">
                                                        <i class="fas fa-user"></i> ${formula.customer || '无'}
                                                    </span>
                                                    <span class="info-item">
                                                        <i class="fas fa-flask"></i> ${formula.ingredients_count || 0} 个成分
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="formula-actions">
                                                <button class="btn btn-sm btn-success me-2" onclick="matchFormula(${formula.id})" title="开始匹配">
                                                    <i class="fas fa-search"></i> 匹配
                                                </button>
                                                <button class="btn btn-sm btn-outline-danger" onclick="deleteToMatchFormula(${formula.id})" title="删除">
                                                    <i class="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                `;
            });
            html += '</div>';
            list.innerHTML = html;

            // 重置选择状态
            document.getElementById('selectAll').checked = false;
            updateBatchControls();
        })
        .catch(error => {
            document.getElementById('formulasList').innerHTML = '<p class="text-danger">加载失败</p>';
        });
}

// 文件选择时自动填充配方名称 - 使用共享组件
// 由FileUploadHandler自动处理

// 删除待匹配配方
function deleteToMatchFormula(formulaId) {
    if (confirm('确定要删除这个待匹配配方吗？')) {
        fetch(`/api/v1/to-match-formulas/${formulaId}`, {
            method: 'DELETE'
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert('success', '配方删除成功！');
                    loadToMatchFormulas();
                } else {
                    showAlert('danger', '删除失败: ' + (data.message || data.detail || '未知错误'));
                }
            })
            .catch(error => {
                console.error('删除失败:', error);
                showAlert('danger', '删除失败: ' + error.message);
            });
    }
}

// 全选/全不选切换
function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('.formula-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
    });

    updateBatchControls();
}

// 更新批量操作控件状态
function updateBatchControls() {
    const checkboxes = document.querySelectorAll('.formula-checkbox');
    const checkedBoxes = document.querySelectorAll('.formula-checkbox:checked');
    const selectAll = document.getElementById('selectAll');
    const selectedCount = document.getElementById('selectedCount');
    const batchActions = document.getElementById('batchActions');

    // 更新选择计数
    selectedCount.textContent = `已选择: ${checkedBoxes.length}`;

    // 更新全选框状态
    if (checkedBoxes.length === 0) {
        selectAll.indeterminate = false;
        selectAll.checked = false;
    } else if (checkedBoxes.length === checkboxes.length) {
        selectAll.indeterminate = false;
        selectAll.checked = true;
    } else {
        selectAll.indeterminate = true;
        selectAll.checked = false;
    }

    // 显示/隐藏批量操作按钮
    if (checkedBoxes.length > 0) {
        batchActions.style.display = 'block';
    } else {
        batchActions.style.display = 'none';
    }
}

// 批量删除配方
function batchDeleteFormulas() {
    const checkedBoxes = document.querySelectorAll('.formula-checkbox:checked');
    if (checkedBoxes.length === 0) {
        showAlert('warning', '请先选择要删除的配方');
        return;
    }

    const formulaIds = Array.from(checkedBoxes).map(cb => parseInt(cb.value));
    const confirmMsg = `确定要删除选中的 ${formulaIds.length} 个配方吗？\\n\\n此操作不可撤销，将同时删除相关的成分数据和匹配记录。`;

    if (confirm(confirmMsg)) {
        // 显示进度提示
        const originalText = event.target.innerHTML;
        event.target.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 删除中...';
        event.target.disabled = true;

        // 调用批量删除API
        fetch('/api/v1/to-match-formulas/batch', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                formula_ids: formulaIds
            })
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || `HTTP ${response.status}: ${response.statusText}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    showAlert('success', `批量删除成功！<br>删除了 ${data.deleted_count} 个配方<br>删除了 ${data.deleted_ingredients_count} 个成分<br>删除了 ${data.deleted_match_records_count} 条匹配记录`);
                    loadToMatchFormulas(); // 刷新列表
                } else {
                    showAlert('danger', '批量删除失败: ' + (data.message || data.detail || '未知错误'));
                }
            })
            .catch(error => {
                console.error('批量删除失败:', error);
                showAlert('danger', '批量删除失败: ' + error.message);
            })
            .finally(() => {
                // 恢复按钮状态
                event.target.innerHTML = originalText;
                event.target.disabled = false;
            });
    }
}

// 提交上传表单 - 使用共享组件
async function submitUploadForm() {
    if (formulaUploadHandler) {
        await formulaUploadHandler.submitUploadForm('uploadForm', {
            modalId: 'uploadModal',
            targetLibrary: 'to_match',
            successCallback: (result) => {
                // 重新加载列表
                loadToMatchFormulas();
            }
        });
    }
}

// 显示提示消息 - 使用共享组件
// showAlert 已在common.js中定义，可直接使用

// 匹配配方
function matchFormula(formulaId) {
    document.getElementById('matchResults').innerHTML = '匹配中，请稍候...';

    // 获取严格模式设置
    const strictMode = document.getElementById('strictMatchMode').checked;

    fetch(`/api/v1/match-formula/${formulaId}?strict_mode=${strictMode}`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayMatchResults(data);
            } else {
                document.getElementById('matchResults').innerHTML = '<p class="text-danger">匹配失败</p>';
            }
        })
        .catch(error => {
            document.getElementById('matchResults').innerHTML = '<p class="text-danger">匹配失败: ' + error.message + '</p>';
        });
}

// 显示详细匹配结果
function displayMatchResults(data) {
    const strictMode = document.getElementById('strictMatchMode').checked;
    const matchModeText = strictMode ? '严格范围匹配' : '全库匹配';
    const matchModeIcon = strictMode ? 'fas fa-filter' : 'fas fa-globe';
    const matchModeColor = strictMode ? 'text-warning' : 'text-info';

    let html = `
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-search"></i> 配方 "${data.source_formula_name}" 的匹配结果</h5>
                                <div class="mb-2">
                                    <span class="badge bg-light text-dark">
                                        <i class="${matchModeIcon} ${matchModeColor}"></i> ${matchModeText}
                                    </span>
                                </div>
                <small class="text-muted">
                    算法: ${data.algorithm} | 
                    找到 ${data.total_matches} 个匹配结果 | 
                    组成权重: ${formatPercentage(data.parameters.composition_weight * 100)} | 
                    比例权重: ${formatPercentage(data.parameters.proportion_weight * 100)}
                </small>
                            </div>
                            <div class="card-body">
                    `;

    if (data.match_results.length === 0) {
        html += '<div class="alert alert-info">未找到匹配的配方</div>';
    } else {
        // 匹配统计信息
        if (data.statistics) {
            html += `
                                <div class="row mb-3">
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6 class="text-success">${formatPercentage(data.statistics.max_similarity * 100)}</h6>
                                            <small class="text-muted">最高相似度</small>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6 class="text-warning">${data.statistics.high_similarity_count || 0}</h6>
                                            <small class="text-muted">高相似度(≥80%)</small>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6 class="text-info">${data.statistics.medium_similarity_count || 0}</h6>
                                            <small class="text-muted">中等相似度(50-80%)</small>
                                        </div>
                                    </div>
                                </div>
                                <hr>
                            `;
        }

        // 匹配结果列表
        html += '<div class="row">';
        data.match_results.forEach((result, index) => {
            const similarityPercent = formatPercentage(result.similarity_score * 100);
            const compositionPercent = formatPercentage(result.composition_similarity * 100);
            const proportionPercent = formatPercentage(result.proportion_similarity * 100);

            // 确定相似度等级和颜色
            let badgeClass = 'bg-secondary';
            let rankIcon = '🥉';
            if (result.similarity_score >= 0.8) {
                badgeClass = 'bg-success';
                rankIcon = index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉';
            } else if (result.similarity_score >= 0.6) {
                badgeClass = 'bg-warning';
            } else if (result.similarity_score >= 0.4) {
                badgeClass = 'bg-info';
            }

            html += `
                                <div class="col-md-12 mb-3">
                                    <div class="card border-left-primary">
                                        <div class="card-body">
                                            <div class="row">
                                                <div class="col-md-8">
                                                        <h6 class="card-title">
                                                        ${rankIcon} 排名 ${index + 1}: ${result.target_formula_name}
                                                        <span class="badge ${badgeClass} ms-2">${similarityPercent}</span>
                                                    </h6>
                                                    <div class="row mt-2">
                                                        <div class="col-md-6">
                                                            <small class="text-muted">
                                                                <i class="fas fa-puzzle-piece"></i> 成分组成相似度: 
                                                                <strong>${compositionPercent}</strong>
                                                            </small>
                                                        </div>
                                                        <div class="col-md-6">
                                                            <small class="text-muted">
                                                                <i class="fas fa-balance-scale"></i> 成分比例相似度: 
                                                                <strong>${proportionPercent}</strong>
                                                            </small>
                                                        </div>
                                                    </div>

                                                </div>
                                                <div class="col-md-4">
                                                    <div class="text-end">
                                                        <button class="btn btn-sm btn-outline-primary mb-2" 
                                                                onclick="showFormulaDetail(${result.target_formula_id}, 'reference')">
                                                            <i class="fas fa-eye"></i> 查看详情
                                                        </button><br>
                                                        <button class="btn btn-sm btn-outline-primary mb-2" 
                                                                onclick="compareFormulas(${data.source_formula_id}, ${result.target_formula_id})">
                                                            <i class="fas fa-code-compare"></i> 对比分析
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>

                                            <!-- 分类相似度详情 -->
                                            <div class="mt-3">
                                                <small class="text-muted">分类相似度:</small>
                                                <div class="row mt-1">
                            `;

            // 显示各分类的相似度
            if (result.category_similarities) {
                Object.entries(result.category_similarities).forEach(([category, similarity]) => {
                    const catPercent = formatPercentage(similarity * 100);
                    let catBadgeClass = 'bg-light text-dark';
                    if (similarity >= 0.8) catBadgeClass = 'bg-success';
                    else if (similarity >= 0.6) catBadgeClass = 'bg-warning';
                    else if (similarity >= 0.3) catBadgeClass = 'bg-info';

                    html += `
                                        <div class="col-auto">
                                            <span class="badge ${catBadgeClass}" style="font-size: 0.7em;">
                                                ${category}: ${catPercent}
                                            </span>
                                        </div>
                                    `;
                });
            }

            html += `
                                                </div>
                                            </div>

                                            <!-- 共同成分预览 -->
                                            <div class="mt-2">
                                                <small class="text-muted">共同成分预览:</small>
                                                <div class="mt-1">
                            `;

            if (result.common_ingredients && result.common_ingredients.length > 0) {
                const displayIngredients = result.common_ingredients.slice(0, 5);
                displayIngredients.forEach(ingredient => {
                    html += `<span class="badge bg-light text-dark me-1" style="font-size: 0.7em;">${ingredient}</span>`;
                });

                if (result.common_ingredients.length > 5) {
                    html += `<span class="text-muted">... 等${result.common_ingredients.length - 5}个</span>`;
                }
            } else {
                html += '<span class="text-muted">无共同成分</span>';
            }

            html += `
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
        });

        html += '</div>';
    }

    html += `
                            </div>
                        </div>
                    `;

    document.getElementById('matchResults').innerHTML = html;
}

// 显示配方详情
function showFormulaDetail(formulaId, type) {
    // 调用API获取配方详情
    fetch(`/api/v1/formula-detail/${formulaId}?formula_type=${type}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            displayFormulaDetailModal(data);
        })
        .catch(error => {
            console.error('获取配方详情失败:', error);
            showAlert('danger', '获取配方详情失败: ' + error.message);
        });
}

// 对比配方
function compareFormulas(sourceId, targetId) {
    // 调用API进行配方对比分析
    fetch('/api/v1/formula-comparison', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source_formula_id: sourceId,
            target_formula_id: targetId
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            displayComparisonModal(data);
        })
        .catch(error => {
            console.error('配方对比分析失败:', error);
            showAlert('danger', '配方对比分析失败: ' + error.message);
        });
}

// 处理成分数据以匹配原配方表格式 - 修复版本
function processIngredientsForDisplay(ingredients) {
    const result = [];
    const compoundGroups = {};

    // 首先按ingredient_id分组
    ingredients.forEach(ing => {
        const ingredientId = ing.ingredient_id;
        if (!compoundGroups[ingredientId]) {
            compoundGroups[ingredientId] = [];
        }
        compoundGroups[ingredientId].push(ing);
    });

    // 按ingredient_id排序处理
    const sortedIngredientIds = Object.keys(compoundGroups).sort((a, b) => parseInt(a) - parseInt(b));

    sortedIngredientIds.forEach(ingredientId => {
        const group = compoundGroups[ingredientId];

        if (group.length === 1) {
            // 单配成分：原料含量和实际成分含量相同，都是分子级
            const ing = group[0];
            result.push({
                type: 'single',
                display_name: ing.standard_chinese_name,
                inci_name: ing.inci_name || '-',
                ingredient_content: ing.ingredient_content || 0,  // 原料含量（对于单配等于实际成分含量）
                actual_component_content: ing.actual_component_content || ing.ingredient_content || 0,  // 实际成分含量（分子级）
                category: ing.purpose || ing.category || '其他'
            });
        } else {
            // 复配成分：显示复配整体和各个分子级成分
            const sortedComponents = group.sort((a, b) => a.ingredient_sequence - b.ingredient_sequence);

            // 获取复配原料含量（相同ingredient_id的所有记录应有相同的ingredient_content，取第一个即可）
            const totalIngredientContent = sortedComponents[0].ingredient_content || 0;

            // 复配名称留空（未来开发复配主要成分识别功能后再显示具体名称）

            // 添加复配整体行
            result.push({
                type: 'compound_header',
                display_name: '',  // 复配标题留空
                inci_name: '-',
                ingredient_content: totalIngredientContent,  // 原料含量（复配整体）
                actual_component_content: '-',  // 复配整体不显示实际成分含量
                category: sortedComponents[0].purpose || sortedComponents[0].category || '其他',
                is_compound_header: true
            });

            // 添加各个分子级成分行
            sortedComponents.forEach(comp => {
                result.push({
                    type: 'compound_component',
                    display_name: comp.standard_chinese_name,
                    inci_name: comp.inci_name || '-',
                    ingredient_content: '-',  // 分子级成分不显示原料含量
                    actual_component_content: comp.actual_component_content || comp.component_content || 0,  // 实际成分含量（分子级）
                    category: '-',  // 复配子项不显示分类
                    is_compound_component: true
                });
            });
        }
    });

    return result;
}

// 显示配方详情模态框
function displayFormulaDetailModal(data) {
    const modalId = 'formulaDetailModal';

    // 删除已存在的模态框
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }

    // 创建详情内容
    const stats = data.statistics;
    let detailContent = `
                        <div class="row">
                            <div class="col-md-12">
                                <div class="card mb-3">
                                    <div class="card-header"><h6><i class="fas fa-info"></i> 基本信息</h6></div>
                                    <div class="card-body">
                                        <table class="table table-borderless table-sm">
                                            <tr><td><strong>配方名称:</strong></td><td>${data.formula_name}</td></tr>
                                            <tr><td><strong>产品类型:</strong></td><td>${data.product_type || '未分类'}</td></tr>
                                            <tr><td><strong>客户:</strong></td><td>${data.customer || '无'}</td></tr>
                                            <tr><td><strong>配方类型:</strong></td><td>${data.formula_type === 'reference' ? '参考配方' : '待匹配配方'}</td></tr>
                                            <tr><td><strong>更新时间:</strong></td><td>${new Date(data.updated_at).toLocaleString()}</td></tr>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="card">
                            <div class="card-header">
                                <h6><i class="fas fa-list"></i> 成分详情</h6>
                                <div class="small text-muted mt-1">
                                    <i class="fas fa-info-circle"></i> 原料含量：完整原料(单配+复配)的含量；实际成分含量：分子级成分的含量<br>
                                    <span class="badge bg-info me-1">蓝色</span>复配整体 
                                    <span class="badge bg-light text-dark">浅色</span>复配分子成分
                                </div>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive" style="max-height: 400px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 0.375rem;">
                                    <table class="table table-striped table-hover table-sm mb-0">
                                        <thead class="table-dark sticky-top">
                                            <tr>
                                                <th>序号</th>
                                                <th>中文名称</th>
                                                <th>INCI名称</th>
                                                <th>原料含量(%)</th>
                                                <th>实际成分含量(%)</th>
                                                <th>分类</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                    `;

    // 按配方表格式显示成分列表
    const processedIngredients = processIngredientsForDisplay(data.ingredients);
    let sequenceNumber = 1;

    processedIngredients.forEach((item, index) => {
        const categoryColors = {
            '防腐剂': 'danger', '乳化剂': 'warning', '增稠剂': 'warning',
            '抗氧化剂': 'warning', '表面活性剂': 'warning'
        };
        const categoryColor = categoryColors[item.category] || 'secondary';

        // 根据成分类型设置不同的样式
        let rowClass = '';
        let sequenceDisplay = '';

        if (item.type === 'single') {
            // 单配成分
            sequenceDisplay = sequenceNumber++;
            rowClass = '';
        } else if (item.type === 'compound_header') {
            // 复配整体
            sequenceDisplay = sequenceNumber++;
            rowClass = 'table-info';  // 浅蓝色背景
        } else if (item.type === 'compound_component') {
            // 复配分子级成分
            sequenceDisplay = '';
            rowClass = 'table-light border-top-0 compound-component';  // 浅灰色背景，无上边框，添加复配子项样式类
        }

        // 格式化含量显示
        const ingredientContentDisplay = item.ingredient_content === '-' ? '-' : formatPercentage(item.ingredient_content);
        const actualContentDisplay = item.actual_component_content === '-' ? '-' : formatPercentage(item.actual_component_content);

        detailContent += `
                            <tr class="${rowClass}">
                                <td>${sequenceDisplay}</td>
                                <td style="max-width: 300px;">${item.display_name}</td>
                                <td>${item.inci_name}</td>
                                <td>${ingredientContentDisplay}</td>
                                <td>${actualContentDisplay}</td>
                                <td><span class="badge bg-${categoryColor}">${item.category}</span></td>
                            </tr>
                        `;
    });

    detailContent += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    `;

    // 创建模态框HTML
    const modalHtml = `
                        <style>
                            .compound-component td:first-child {
                                padding-left: 2rem !important;
                            }
                            .compound-component td:nth-child(2) {
                                padding-left: 2rem !important;
                                text-indent: -1rem;
                                padding-right: 1rem;
                                word-wrap: break-word;
                                white-space: normal;
                                line-height: 1.4;
                            }
                        </style>
                        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-xl">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h5 class="modal-title">
                                            <i class="fas fa-info-circle"></i> 
                                            配方详情 - ${data.formula_name}
                                        </h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        ${detailContent}
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

    // 添加到页面并显示
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();

    // 模态框关闭时清理
    document.getElementById(modalId).addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// 生成分类分组HTML
function generateCategoryGroupHTML(groupedData, compounds_detail, colorClass) {
    let html = '';

    // 分类优先级顺序
    const categoryOrder = ['防腐剂', '乳化剂', '增稠剂', '抗氧化剂', '表面活性剂', '其他'];
    
    
    const categoryColors = {
        '防腐剂': 'danger',
        '乳化剂': 'warning',
        '增稠剂': 'warning',
        '抗氧化剂': 'warning',
        '表面活性剂': 'warning',
        '其他': 'secondary'
    };



    categoryOrder.forEach(category => {
        if (groupedData[category] && groupedData[category].length > 0) {
            const ingredients = groupedData[category];
            const categoryColor = categoryColors[category];
            const collapseId = `collapse-${category}-${Math.random().toString(36).substr(2, 9)}`;

            html += `
                                <div class="mb-2">
                                    <div class="d-flex align-items-center">
                                        <button class="btn btn-sm btn-outline-${categoryColor} flex-grow-1 text-start" 
                                                type="button" 
                                                data-bs-toggle="collapse" 
                                                data-bs-target="#${collapseId}">
                                            <i class="fas fa-chevron-down me-2"></i>
                                            <strong>${category}</strong> 
                                            <span class="badge bg-${categoryColor} ms-2">${ingredients.length}</span>
                                        </button>
                                    </div>
                                    <div class="collapse show" id="${collapseId}">
                                        <div class="mt-2 ps-3">
                            `;

            ingredients.forEach(ingredientObj => {
                const ingredient = ingredientObj.name;
                if (ingredient.startsWith('复配_')) {
                    // 复配成分显示为小列表
                    const compoundComponents = compounds_detail[ingredient] || [];
                    html += `
                        <div class="card mb-2">
                            <div class="card-header py-1 px-2 bg-${categoryColor} text-white">
                                <small><strong>${ingredient}</strong></small>
                            </div>
                            <div class="card-body py-1 px-2">
                                <small>
                                    `;
                    if (compoundComponents.length > 0) {
                        compoundComponents.forEach(comp => {
                            html += `<span class="badge bg-secondary me-1 mb-1">${comp}</span>`;
                        });
                    } else {
                        html += '<span class="text-muted">无详细成分</span>';
                    }
                    html += `
                                </small>
                            </div>
                        </div>
                                    `;
                } else {
                    // 单配成分
                    html += `<span class="badge bg-${categoryColor} me-1 mb-1">${ingredient}</span>`;
                }
            });

            html += `
                                        </div>
                                    </div>
                                </div>
                            `;
        }
    });

    return html;
}

// 显示对比分析模态框
function displayComparisonModal(data) {
    const modalId = 'comparisonModal';

    // 删除已存在的模态框
    const existingModal = document.getElementById(modalId);
    if (existingModal) {
        existingModal.remove();
    }

    const similarity = data.similarity_analysis;
    const ingredients = data.ingredients_analysis;

    // 创建对比内容
    let comparisonContent = `
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <div class="card border-primary">
                                    <div class="card-header bg-primary text-white">
                                        <h6><i class="fas fa-flask"></i> ${data.source_formula.name}</h6>
                                        <small>${data.source_formula.type}</small>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>产品类型:</strong> ${data.source_formula.product_type || '未分类'}</p>
                                        <p><strong>客户:</strong> ${data.source_formula.customer || '无'}</p>
                                        <p><strong>成分数:</strong> ${data.source_formula.ingredients_count}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card border-purple">
                                    <div class="card-header bg-purple text-white">
                                        <h6><i class="fas fa-database"></i> ${data.target_formula.name}</h6>
                                        <small>${data.target_formula.type}</small>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>产品类型:</strong> ${data.target_formula.product_type || '未分类'}</p>
                                        <p><strong>客户:</strong> ${data.target_formula.customer || '无'}</p>
                                        <p><strong>成分数:</strong> ${data.target_formula.ingredients_count}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row mb-4">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-header">
                                        <h6><i class="fas fa-chart-line"></i> 相似度分析</h6>
                                    </div>
                                    <div class="card-body">
                                        <div class="row text-center">
                                            <div class="col-md-3">
                                                <h4 class="text-primary">${formatPercentage(similarity.total_similarity * 100)}</h4>
                                                <small class="text-muted">总相似度</small>
                                            </div>
                                            <div class="col-md-3">
                                                <h5 class="text-info">${formatPercentage(similarity.composition_similarity * 100)}</h5>
                                                <small class="text-muted">成分组成相似度</small>
                                            </div>
                                            <div class="col-md-3">
                                                <h5 class="text-warning">${formatPercentage(similarity.proportion_similarity * 100)}</h5>
                                                <small class="text-muted">成分比例相似度</small>
                                            </div>
                                            <div class="col-md-3">
                                                <h5 class="text-success">${ingredients.common_count}</h5>
                                                <small class="text-muted">共同成分数</small>
                                            </div>
                                        </div>

                                        <hr>

                                        <h6>分类相似度:</h6>
                                        <div class="row">
                    `;

    // 显示分类相似度
    Object.entries(similarity.category_similarities).forEach(([category, sim]) => {
        const percentage = formatPercentage(sim * 100);
        let badgeClass = 'secondary';
        if (sim >= 0.8) badgeClass = 'success';
        else if (sim >= 0.6) badgeClass = 'warning';
        else if (sim >= 0.3) badgeClass = 'info';

        comparisonContent += `
                            <div class="col-md-3 mb-2">
                                <span class="badge bg-${badgeClass}">${category}: ${percentage}</span>
                            </div>
                        `;
    });

    comparisonContent += `
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="row">
                            <div class="col-md-4">
                                <div class="card h-100">
                                    <div class="card-header bg-success text-white">
                                        <h6><i class="fas fa-check-circle"></i> 共同成分 (${ingredients.common_count})</h6>
                                    </div>
                                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                    `;

    // 使用分类分组显示
    if (ingredients.common_ingredients_grouped && Object.keys(ingredients.common_ingredients_grouped).length > 0) {
        const compounds_detail = {...ingredients.source_compounds_detail, ...ingredients.target_compounds_detail};
        comparisonContent += generateCategoryGroupHTML(ingredients.common_ingredients_grouped, compounds_detail, 'light text-dark');
    } else {
        comparisonContent += '<p class="text-muted">无共同成分</p>';
    }

    comparisonContent += `
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card h-100">
                                    <div class="card-header bg-primary text-white">
                                        <h6><i class="fas fa-flask"></i> 源配方独有 (${ingredients.source_only_count})</h6>
                                    </div>
                                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                    `;

    // 使用分类分组显示
    if (ingredients.source_only_grouped && Object.keys(ingredients.source_only_grouped).length > 0) {
        comparisonContent += generateCategoryGroupHTML(ingredients.source_only_grouped, ingredients.source_compounds_detail, 'primary');
    } else {
        comparisonContent += '<p class="text-muted">无独有成分</p>';
    }

    comparisonContent += `
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card h-100">
                                    <div class="card-header bg-purple text-white">
                                        <h6><i class="fas fa-database"></i> 目标配方独有 (${ingredients.target_only_count})</h6>
                                    </div>
                                    <div class="card-body" style="max-height: 300px; overflow-y: auto;">
                    `;

    // 使用分类分组显示
    if (ingredients.target_only_grouped && Object.keys(ingredients.target_only_grouped).length > 0) {
        comparisonContent += generateCategoryGroupHTML(ingredients.target_only_grouped, ingredients.target_compounds_detail, 'purple');
    } else {
        comparisonContent += '<p class="text-muted">无独有成分</p>';
    }

    comparisonContent += `
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- 新增：原料对比分析区域 -->
                        <div class="row mt-4">
                            <div class="col-md-12">
                                <div class="card">
                                    <div class="card-header">
                                        <h6><i class="fas fa-balance-scale"></i> 共有原料对比分析</h6>
                                        <small class="text-muted">显示两个配方中共有原料的实际含量对比（复配已拆分为单一原料并合并同类项）</small>
                                    </div>
                                    <div class="card-body">
                    `;

    // 添加原料对比内容
    if (data.ingredient_comparison && data.ingredient_comparison.common_ingredients && data.ingredient_comparison.common_ingredients.length > 0) {
        const ingredientComparison = data.ingredient_comparison;
        comparisonContent += `
                                        <div class="mb-3">
                                            <div class="row text-center">
                                                <div class="col-md-4">
                                                    <div class="text-primary">
                                                        <h6>${data.source_formula.name}</h6>
                                                        <small class="text-muted">待匹配配方</small>
                                                    </div>
                                                </div>
                                                <div class="col-md-4">
                                                    <h6 class="text-success">共有原料 (${ingredientComparison.common_count})</h6>
                                                    <small class="text-muted">按含量排序</small>
                                                </div>
                                                <div class="col-md-4">
                                                    <div class="text-purple">
                                                        <h6>${data.target_formula.name}</h6>
                                                        <small class="text-muted">参考配方</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                        
                                        <div class="ingredient-comparison-list" style="max-height: 400px; overflow-y: auto;">
        `;

        // 生成每个共有原料的对比进度条
        ingredientComparison.common_ingredients.forEach((ingredient, index) => {
            const sourcePercent = ingredient.source_content;
            const targetPercent = ingredient.target_content;
            
            // 计算进度条的最大值，用于比例显示
            const maxPercent = Math.max(sourcePercent, targetPercent);
            const sourceWidth = maxPercent > 0 ? (sourcePercent / maxPercent * 100) : 0;
            const targetWidth = maxPercent > 0 ? (targetPercent / maxPercent * 100) : 0;

            comparisonContent += `
                                            <div class="ingredient-comparison-item mb-3 p-3 border rounded">
                                                <div class="row align-items-center">
                                                    <div class="col-md-4 text-end">
                                                        <!-- 左侧（待匹配配方）进度条 -->
                                                        <div class="d-flex align-items-center justify-content-end">
                                                            <span class="ingredient-percent me-2 text-primary">${formatPercentage(sourcePercent)}</span>
                                                            <div class="progress ingredient-progress-left flex-grow-1" style="max-width: 200px;">
                                                                <div class="progress-bar bg-primary" style="width: ${sourceWidth}%"></div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                    <div class="col-md-4 text-center">
                                                        <strong class="ingredient-name">${ingredient.name}</strong>
                                                    </div>
                                                    <div class="col-md-4">
                                                        <!-- 右侧（参考配方）进度条 -->
                                                        <div class="d-flex align-items-center">
                                                            <div class="progress ingredient-progress-right flex-grow-1" style="max-width: 200px;">
                                                                <div class="progress-bar bg-purple" style="width: ${targetWidth}%"></div>
                                                            </div>
                                                            <span class="ingredient-percent ms-2 text-purple">${formatPercentage(targetPercent)}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
            `;
        });

        comparisonContent += `
                                        </div>
        `;
    } else {
        comparisonContent += `
                                        <div class="text-center text-muted py-4">
                                            <i class="fas fa-info-circle fa-2x mb-3"></i>
                                            <h6>无共有原料</h6>
                                            <p>两个配方没有共同的原料成分</p>
                                        </div>
        `;
    }

    comparisonContent += `
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

    // 创建模态框HTML
    const modalHtml = `
                        <div class="modal fade" id="${modalId}" tabindex="-1" aria-hidden="true">
                            <div class="modal-dialog modal-xl">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h5 class="modal-title">
                                            <i class="fas fa-code-compare"></i> 
                                            配方对比分析
                                        </h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        ${comparisonContent}
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                                        <button type="button" class="btn btn-primary" onclick="exportComparison()">
                                            <i class="fas fa-download"></i> 导出对比
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

    // 添加到页面并显示
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();

    // 模态框关闭时清理
    document.getElementById(modalId).addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// 导出对比结果（占位函数）
function exportComparison() {
    showAlert('info', '导出对比结果功能开发中...');
}

// 客户自动完成功能 - 使用共享组件
// 由CustomerAutocomplete类处理，在initializeUploadMatchPage中初始化

// 客户输入框功能在共享组件中处理
// 移除重复代码

// 登出功能在common.js中已定义
// 移除重复代码

// 显示快速映射模态框
async function showQuickMappingModal() {
    const formulaNameInput = document.getElementById('formulaName');
    const formulaName = formulaNameInput.value.trim();
    
    // 如果有配方名称，自动填入
    if (formulaName) {
        document.getElementById('mappingFromName').value = formulaName;
    }
    
    // 动态填充产品类型下拉菜单
    await formulaUploadHandler.productTypeRecognizer.populateProductTypeDropdown('mappingToProductType');
    
    const modal = new bootstrap.Modal(document.getElementById('quickMappingModal'));
    modal.show();
}

// 提交快速映射
async function submitQuickMapping() {
    const fromName = document.getElementById('mappingFromName').value.trim();
    const toProductType = document.getElementById('mappingToProductType').value;
    
    if (!fromName) {
        showAlert('warning', '请输入配方名称');
        return;
    }
    
    if (!toProductType) {
        showAlert('warning', '请选择目标产品类型');
        return;
    }
    
    if (!formulaUploadHandler || !formulaUploadHandler.productTypeRecognizer) {
        showAlert('error', '产品类型识别器未初始化');
        return;
    }
    
    // 显示加载状态
    const submitBtn = document.querySelector('#quickMappingModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>添加中...';
    submitBtn.disabled = true;
    
    try {
        const success = await formulaUploadHandler.productTypeRecognizer.addProductTypeMapping(fromName, toProductType);
        
        if (success) {
            showAlert('success', `映射添加成功！<br>"${fromName}" → "${toProductType}"`);
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('quickMappingModal'));
            modal.hide();
            
            // 重置表单
            document.getElementById('quickMappingForm').reset();
            
            // 如果输入框中的配方名称与刚才添加的映射匹配，自动识别
            const currentFormulaName = document.getElementById('formulaName').value.trim();
            if (currentFormulaName && (currentFormulaName.includes(fromName) || fromName.includes(currentFormulaName))) {
                setTimeout(() => {
                    manualRecognizeProductType();
                }, 500);
            }
        } else {
            showAlert('danger', '映射添加失败，请重试');
        }
    } catch (error) {
        console.error('添加映射失败:', error);
        showAlert('danger', '映射添加失败：' + error.message);
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}