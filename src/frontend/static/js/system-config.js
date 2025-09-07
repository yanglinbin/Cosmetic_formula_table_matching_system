// 页面加载时获取当前配置
document.addEventListener('DOMContentLoaded', function () {
    loadCurrentConfig();
    loadProductTypesConfig();
    loadSystemStats();
    loadProductTypeMappings(); // 加载产品类型映射
    loadUsers(); // 加载用户列表
});

// 加载当前配置
async function loadCurrentConfig() {
    try {
        // 加载分类权重
        const weightResponse = await fetch('/api/v1/config/category-weights');
        const weightData = await weightResponse.json();
        if (weightData.success) {
            const weights = weightData.data;
            for (const [category, weight] of Object.entries(weights)) {
                const input = document.getElementById(`weight-${category}`);
                if (input) input.value = weight;
            }
            updateWeightSum();
        }

        // 加载匹配参数
        const paramResponse = await fetch('/api/v1/config/matching-parameters');
        const paramData = await paramResponse.json();
        if (paramData.success) {
            const params = paramData.data;
            for (const [param, value] of Object.entries(params)) {
                const input = document.getElementById(param);
                if (input) input.value = value;
            }
            updateCompositionSum();
        }
    } catch (error) {
        console.error('加载配置失败:', error);
        showStatus('加载配置失败: ' + error.message, 'danger');
    }
}

// 加载系统统计
async function loadSystemStats() {
    try {
        const response = await fetch('/api/v1/stats');
        const data = await response.json();
        document.getElementById('catalog-count').textContent = data.ingredient_catalog_count.toLocaleString();
        document.getElementById('reference-formulas-count').textContent = data.reference_formulas_count.toLocaleString();
        // 计算产品类型数量（从配置中获取）
        let productTypesCount = 0;
        if (systemProductTypesConfig) {
            productTypesCount = Object.keys(systemProductTypesConfig).length;
        }
        document.getElementById('product-types-count').textContent = productTypesCount.toLocaleString();
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// 更新权重总和
function updateWeightSum() {
    const categories = ['防腐剂', '乳化剂', '增稠剂', '抗氧化剂', '表面活性剂', '其他'];
    let sum = 0;
    categories.forEach(category => {
        const input = document.getElementById(`weight-${category}`);
        if (input && input.value) {
            sum += parseFloat(input.value);
        }
    });

    const sumElement = document.getElementById('weight-sum');
    const warningElement = document.getElementById('weight-warning');

    sumElement.textContent = sum.toFixed(2);

    if (Math.abs(sum - 1.0) < 0.01) {
        sumElement.className = 'weight-sum valid';
        warningElement.style.display = 'none';
    } else {
        sumElement.className = 'weight-sum';
        warningElement.style.display = 'inline';
    }
}

// 更新组成权重总和
function updateCompositionSum() {
    const compositionWeight = parseFloat(document.getElementById('composition_weight').value) || 0;
    const proportionWeight = parseFloat(document.getElementById('proportion_weight').value) || 0;
    const sum = compositionWeight + proportionWeight;

    const sumElement = document.getElementById('composition-sum');
    const warningElement = document.getElementById('composition-warning');

    sumElement.textContent = sum.toFixed(2);

    if (Math.abs(sum - 1.0) < 0.01) {
        sumElement.style.color = '#198754';
        warningElement.style.display = 'none';
    } else {
        sumElement.style.color = '#dc3545';
        warningElement.style.display = 'inline';
    }
}

// 显示状态消息（使用全局通知系统）
function showStatus(message, type) {
    GlobalNotificationSystem.showNotification(type, message);
}

// 保存分类权重
async function saveCategoryWeights() {
    try {
        const categories = ['防腐剂', '乳化剂', '增稠剂', '抗氧化剂', '表面活性剂', '其他'];
        const weights = {};

        categories.forEach(category => {
            const input = document.getElementById(`weight-${category}`);
            weights[category] = parseFloat(input.value) || 0;
        });

        const response = await fetch('/api/v1/config/category-weights', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(weights)
        });

        const data = await response.json();
        if (data.success) {
            showStatus('分类权重保存成功！', 'success');
        } else {
            showStatus('保存失败: ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('保存分类权重失败:', error);
        showStatus('保存失败: ' + error.message, 'danger');
    }
}

// 保存匹配参数
async function saveMatchingParams() {
    try {
        const params = {
            composition_weight: parseFloat(document.getElementById('composition_weight').value) || 0,
            proportion_weight: parseFloat(document.getElementById('proportion_weight').value) || 0,
            compound_threshold: parseFloat(document.getElementById('compound_threshold').value) || 0,
            min_similarity_threshold: parseFloat(document.getElementById('min_similarity_threshold').value) || 0
        };

        const response = await fetch('/api/v1/config/matching-parameters', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(params)
        });

        const data = await response.json();
        if (data.success) {
            showStatus('匹配参数保存成功！', 'success');
        } else {
            showStatus('保存失败: ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('保存匹配参数失败:', error);
        showStatus('保存失败: ' + error.message, 'danger');
    }
}

// 保存所有配置
async function saveAllConfig() {
    await saveCategoryWeights();
    await saveMatchingParams();
}

// 重置为默认配置
async function resetAllConfig() {
    if (confirm('确定要重置所有配置为默认值吗？')) {
        try {
            const response = await fetch('/api/v1/config/initialize', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                showStatus('配置已重置为默认值！', 'success');
                // 重新加载配置
                setTimeout(() => {
                    loadCurrentConfig();
                    loadProductTypesConfig();
                }, 1000);
            } else {
                showStatus('重置失败: ' + data.message, 'danger');
            }
        } catch (error) {
            console.error('重置配置失败:', error);
            showStatus('重置失败: ' + error.message, 'danger');
        }
    }
}

// 产品类型配置相关变量
let systemProductTypesConfig = {};
let categoryCounter = 0;

// 加载产品类型配置
async function loadProductTypesConfig() {
    try {
        const response = await fetch('/api/v1/config/product-types');
        const data = await response.json();
        if (data.success) {
            systemProductTypesConfig = data.data;
            renderProductTypesConfig();
            // 更新统计数据中的产品类型数量
            const productTypesCount = Object.keys(systemProductTypesConfig).length;
            document.getElementById('product-types-count').textContent = productTypesCount.toLocaleString();
        }
    } catch (error) {
        console.error('加载产品类型配置失败:', error);
        showStatus('加载产品类型配置失败: ' + error.message, 'danger');
    }
}

// 渲染产品类型配置界面
function renderProductTypesConfig() {
    const container = document.getElementById('productTypesContainer');
    let html = '';

    for (const [category, subcategories] of Object.entries(systemProductTypesConfig)) {
        const categoryId = `category_${categoryCounter++}`;
        html += `
                            <div class="card mb-3" id="${categoryId}">
                                <div class="card-header d-flex justify-content-between align-items-center">
                                    <div class="flex-grow-1">
                                        <input type="text" class="form-control category-name" value="${category}" placeholder="产品大类名称" style="display: inline-block; width: 200px;">
                                    </div>
                                    <button class="btn btn-sm btn-danger" onclick="removeProductCategory('${categoryId}')">
                                        <i class="fas fa-trash"></i> 删除大类
                                    </button>
                                </div>
                                <div class="card-body">
                                    <div class="mb-3">
                                        <label class="form-label">细分类型：</label>
                                        <div class="subcategories-container" id="${categoryId}_subcategories">
                        `;

        subcategories.forEach((subcategory, index) => {
            html += `
                                <div class="input-group mb-2 subcategory-item">
                                    <input type="text" class="form-control subcategory-name" value="${subcategory}" placeholder="细分类型名称">
                                    <button class="btn btn-outline-danger btn-sm" type="button" onclick="removeSubcategory(this)">
                                        <i class="fas fa-times"></i>
                                    </button>
                                </div>
                            `;
        });

        html += `
                                        </div>
                                        <button class="btn btn-sm btn-outline-success" onclick="addSubcategory('${categoryId}_subcategories')">
                                            <i class="fas fa-plus"></i> 添加细分类型
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
    }

    container.innerHTML = html;
}

// 添加产品大类
function addProductCategory() {
    const categoryId = `category_${categoryCounter++}`;
    const container = document.getElementById('productTypesContainer');

    const categoryDiv = document.createElement('div');
    categoryDiv.className = 'card mb-3';
    categoryDiv.id = categoryId;
    categoryDiv.innerHTML = `
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <div class="flex-grow-1">
                                <input type="text" class="form-control category-name" value="" placeholder="产品大类名称" style="display: inline-block; width: 200px;">
                            </div>
                            <button class="btn btn-sm btn-danger" onclick="removeProductCategory('${categoryId}')">
                                <i class="fas fa-trash"></i> 删除大类
                            </button>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label class="form-label">细分类型：</label>
                                <div class="subcategories-container" id="${categoryId}_subcategories">
                                </div>
                                <button class="btn btn-sm btn-outline-success" onclick="addSubcategory('${categoryId}_subcategories')">
                                    <i class="fas fa-plus"></i> 添加细分类型
                                </button>
                            </div>
                        </div>
                    `;

    container.appendChild(categoryDiv);
}

// 删除产品大类
function removeProductCategory(categoryId) {
    if (confirm('确定要删除这个产品大类吗？')) {
        const categoryDiv = document.getElementById(categoryId);
        if (categoryDiv) {
            categoryDiv.remove();
        }
    }
}

// 添加细分类型
function addSubcategory(containerId) {
    const container = document.getElementById(containerId);
    const subcategoryDiv = document.createElement('div');
    subcategoryDiv.className = 'input-group mb-2 subcategory-item';
    subcategoryDiv.innerHTML = `
                        <input type="text" class="form-control subcategory-name" value="" placeholder="细分类型名称">
                        <button class="btn btn-outline-danger btn-sm" type="button" onclick="removeSubcategory(this)">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
    container.appendChild(subcategoryDiv);
}

// 删除细分类型
function removeSubcategory(button) {
    const subcategoryDiv = button.closest('.subcategory-item');
    if (subcategoryDiv) {
        subcategoryDiv.remove();
    }
}

// 保存产品类型配置
async function saveProductTypes() {
    try {
        const productTypes = {};

        // 收集所有产品大类和细分类型
        const categoryCards = document.querySelectorAll('#productTypesContainer .card');

        categoryCards.forEach(card => {
            const categoryNameInput = card.querySelector('.category-name');
            const categoryName = categoryNameInput.value.trim();

            if (categoryName) {
                const subcategoryInputs = card.querySelectorAll('.subcategory-name');
                const subcategories = [];

                subcategoryInputs.forEach(input => {
                    const subcategoryName = input.value.trim();
                    if (subcategoryName) {
                        subcategories.push(subcategoryName);
                    }
                });

                productTypes[categoryName] = subcategories;
            }
        });

        // 发送到服务器
        const response = await fetch('/api/v1/config/product-types', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(productTypes)
        });

        const data = await response.json();
        if (data.success) {
            showStatus('产品类型配置保存成功！', 'success');
            systemProductTypesConfig = productTypes;
        } else {
            showStatus('保存失败: ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('保存产品类型配置失败:', error);
        showStatus('保存失败: ' + error.message, 'danger');
    }
}

// 登出功能
async function logout() {
    try {
        const response = await fetch('/api/v1/auth/logout', {
            method: 'POST'
        });

        const data = await response.json();
        if (data.success) {
            window.location.href = '/';
        } else {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('登出失败:', error);
        window.location.href = '/';
    }
}

// ===========================================
// 产品类型映射管理相关函数
// ===========================================

// 存储映射数据和产品类型数据
let allMappings = {};
let productTypeMappingsConfig = {};

// 加载产品类型映射数据
async function loadProductTypeMappings() {
    try {
        const response = await fetch('/api/v1/config/product-type-mappings');
        const data = await response.json();
        
        if (data.success) {
            allMappings = data.data || {};
            updateMappingsTable(allMappings);
            updateMappingsCount();
        } else {
            console.error('加载映射数据失败:', data.message);
            showStatus('加载映射数据失败', 'danger');
        }
    } catch (error) {
        console.error('加载映射数据失败:', error);
        showStatus('加载映射数据失败: ' + error.message, 'danger');
    }
}

// 更新映射表格显示
function updateMappingsTable(mappings) {
    const tbody = document.getElementById('mappingsTableBody');
    
    if (Object.keys(mappings).length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center text-muted">
                    <i class="fas fa-info-circle me-2"></i>暂无映射数据
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    Object.entries(mappings).forEach(([fromName, toProductType]) => {
        html += `
            <tr>
                <td>
                    <strong>${escapeHtml(fromName)}</strong>
                    <br><small class="text-muted">匹配包含此关键词的配方名</small>
                </td>
                <td>
                    <span class="badge bg-primary">${escapeHtml(toProductType)}</span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="showEditMappingModal('${escapeHtml(fromName)}', '${escapeHtml(toProductType)}')" title="编辑">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="confirmDeleteMapping('${escapeHtml(fromName)}')" title="删除">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 更新映射数量统计
function updateMappingsCount() {
    const count = Object.keys(allMappings).length;
    document.getElementById('mappingsCount').textContent = count;
    
    // 更新系统统计中的映射数量
    const mappingsCountElement = document.getElementById('mappings-count');
    if (mappingsCountElement) {
        mappingsCountElement.textContent = count.toLocaleString();
    }
}

// 搜索映射
function searchMappings() {
    const searchTerm = document.getElementById('mappingSearchInput').value.toLowerCase();
    
    if (!searchTerm) {
        updateMappingsTable(allMappings);
        return;
    }
    
    const filteredMappings = {};
    Object.entries(allMappings).forEach(([fromName, toProductType]) => {
        if (fromName.toLowerCase().includes(searchTerm) || 
            toProductType.toLowerCase().includes(searchTerm)) {
            filteredMappings[fromName] = toProductType;
        }
    });
    
    updateMappingsTable(filteredMappings);
}

// 显示添加映射模态框
async function showAddMappingModal() {
    // 加载产品类型配置用于下拉菜单
    await loadProductTypesForDropdown('addMappingToProductType');
    
    // 清空表单
    document.getElementById('addMappingForm').reset();
    
    const modal = new bootstrap.Modal(document.getElementById('addMappingModal'));
    modal.show();
}

// 显示编辑映射模态框
async function showEditMappingModal(fromName, toProductType) {
    // 加载产品类型配置用于下拉菜单
    await loadProductTypesForDropdown('editMappingToProductType');
    
    // 填充表单
    document.getElementById('editMappingOriginalFromName').value = fromName;
    document.getElementById('editMappingFromName').value = fromName;
    document.getElementById('editMappingToProductType').value = toProductType;
    
    const modal = new bootstrap.Modal(document.getElementById('editMappingModal'));
    modal.show();
}

// 为下拉菜单加载产品类型
async function loadProductTypesForDropdown(selectId) {
    try {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        // 清空现有选项
        select.innerHTML = '<option value="">请选择目标产品类型</option>';
        
        // 获取产品类型配置
        if (!productTypeMappingsConfig || Object.keys(productTypeMappingsConfig).length === 0) {
            const response = await fetch('/api/v1/config/product-types');
            const data = await response.json();
            if (data.success) {
                productTypeMappingsConfig = data.data || {};
            }
        }
        
        // 填充选项
        Object.entries(productTypeMappingsConfig).forEach(([category, subcategories]) => {
            if (subcategories && subcategories.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = category;
                
                subcategories.forEach(subcategory => {
                    const option = document.createElement('option');
                    option.value = `${category}-${subcategory}`;
                    option.textContent = subcategory;
                    optgroup.appendChild(option);
                });
                
                select.appendChild(optgroup);
            }
        });
        
    } catch (error) {
        console.error('加载产品类型失败:', error);
    }
}

// 提交添加映射
async function submitAddMapping() {
    const fromName = document.getElementById('addMappingFromName').value.trim();
    const toProductType = document.getElementById('addMappingToProductType').value;
    
    if (!fromName) {
        showStatus('请输入配方名称', 'warning');
        return;
    }
    
    if (!toProductType) {
        showStatus('请选择目标产品类型', 'warning');
        return;
    }
    
    // 检查是否已存在相同映射
    if (allMappings.hasOwnProperty(fromName)) {
        if (!confirm(`映射 "${fromName}" 已存在，是否覆盖？`)) {
            return;
        }
    }
    
    const submitBtn = document.querySelector('#addMappingModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>添加中...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/v1/config/product-type-mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_name: fromName,
                to_product_type: toProductType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(`映射添加成功："${fromName}" → "${toProductType}"`, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addMappingModal'));
            modal.hide();
            
            // 重新加载映射数据
            await loadProductTypeMappings();
            
        } else {
            showStatus('映射添加失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('添加映射失败:', error);
        showStatus('映射添加失败：' + error.message, 'danger');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 提交编辑映射
async function submitEditMapping() {
    const originalFromName = document.getElementById('editMappingOriginalFromName').value;
    const fromName = document.getElementById('editMappingFromName').value.trim();
    const toProductType = document.getElementById('editMappingToProductType').value;
    
    if (!fromName) {
        showStatus('请输入配方名称', 'warning');
        return;
    }
    
    if (!toProductType) {
        showStatus('请选择目标产品类型', 'warning');
        return;
    }
    
    const submitBtn = document.querySelector('#editMappingModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
    submitBtn.disabled = true;
    
    try {
        // 如果配方名称改变了，需要删除原来的并添加新的
        if (originalFromName !== fromName) {
            // 删除原映射
            await fetch('/api/v1/config/product-type-mappings', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    from_name: originalFromName
                })
            });
        }
        
        // 添加新映射（或更新现有映射）
        const response = await fetch('/api/v1/config/product-type-mappings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_name: fromName,
                to_product_type: toProductType
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(`映射更新成功："${fromName}" → "${toProductType}"`, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('editMappingModal'));
            modal.hide();
            
            // 重新加载映射数据
            await loadProductTypeMappings();
            
        } else {
            showStatus('映射更新失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('更新映射失败:', error);
        showStatus('映射更新失败：' + error.message, 'danger');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 确认删除映射
function confirmDeleteMapping(fromName) {
    if (confirm(`确定要删除映射 "${fromName}" 吗？`)) {
        deleteMapping(fromName);
    }
}

// 删除映射
async function deleteMapping(fromName) {
    try {
        const response = await fetch('/api/v1/config/product-type-mappings', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                from_name: fromName
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(`映射删除成功："${fromName}"`, 'success');
            
            // 重新加载映射数据
            await loadProductTypeMappings();
            
        } else {
            showStatus('映射删除失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('删除映射失败:', error);
        showStatus('映射删除失败：' + error.message, 'danger');
    }
}

// 清空所有映射
async function clearAllMappings() {
    const count = Object.keys(allMappings).length;
    if (count === 0) {
        showStatus('没有映射需要清空', 'info');
        return;
    }
    
    if (!confirm(`确定要清空所有 ${count} 条映射吗？此操作不可撤销！`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/config/product-type-mappings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('所有映射已清空', 'success');
            
            // 重新加载映射数据
            await loadProductTypeMappings();
            
        } else {
            showStatus('清空映射失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('清空映射失败:', error);
        showStatus('清空映射失败：' + error.message, 'danger');
    }
}

// HTML转义工具函数
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// ===========================================
// 用户管理相关函数
// ===========================================

// 存储用户数据
let allUsers = [];

// 加载用户列表
async function loadUsers() {
    try {
        const response = await fetch('/api/v1/users');
        const data = await response.json();
        
        if (data.success) {
            allUsers = data.data || [];
            updateUsersTable(allUsers);
            updateUsersCount();
        } else {
            console.error('加载用户数据失败:', data.message);
            showStatus('加载用户数据失败', 'danger');
        }
    } catch (error) {
        console.error('加载用户数据失败:', error);
        showStatus('加载用户数据失败: ' + error.message, 'danger');
    }
}

// 更新用户表格显示
function updateUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">
                    <i class="fas fa-info-circle me-2"></i>暂无用户数据
                </td>
            </tr>
        `;
        return;
    }
    
    let html = '';
    users.forEach(user => {
        const lastLogin = user.last_login ? 
            new Date(user.last_login).toLocaleString('zh-CN') : '从未登录';
        const isActive = user.is_active;
        const roleText = user.role === 'admin' ? '管理员' : '普通用户';
        const statusBadge = isActive ? 
            '<span class="badge bg-success">激活</span>' : 
            '<span class="badge bg-danger">停用</span>';
        
        html += `
            <tr>
                <td>${user.id}</td>
                <td>
                    <strong>${escapeHtml(user.username)}</strong>
                    ${user.role === 'admin' ? '<i class="fas fa-crown text-warning ms-1" title="管理员"></i>' : ''}
                </td>
                <td>
                    <span class="badge ${user.role === 'admin' ? 'bg-warning' : 'bg-info'}">${roleText}</span>
                </td>
                <td>${statusBadge}</td>
                <td>
                    <small class="text-muted">${lastLogin}</small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button class="btn btn-outline-primary" onclick="showEditUserModal(${user.id})" title="编辑">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-warning" onclick="showResetPasswordModal(${user.id})" title="重置密码">
                            <i class="fas fa-key"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="confirmDeleteUser(${user.id})" title="删除">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// 更新用户数量统计
function updateUsersCount() {
    const count = allUsers.length;
    document.getElementById('usersCount').textContent = count;
    
    // 更新系统统计中的用户数量
    const usersCountElement = document.getElementById('users-count');
    if (usersCountElement) {
        usersCountElement.textContent = count.toLocaleString();
    }
}

// 搜索用户
function searchUsers() {
    const searchTerm = document.getElementById('userSearchInput').value.toLowerCase();
    
    if (!searchTerm) {
        updateUsersTable(allUsers);
        return;
    }
    
    const filteredUsers = allUsers.filter(user => 
        user.username.toLowerCase().includes(searchTerm) ||
        user.role.toLowerCase().includes(searchTerm)
    );
    
    updateUsersTable(filteredUsers);
}

// 显示添加用户模态框
function showAddUserModal() {
    // 清空表单
    document.getElementById('addUserForm').reset();
    
    const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
    modal.show();
}

// 提交添加用户
async function submitAddUser() {
    const username = document.getElementById('addUserUsername').value.trim();
    const password = document.getElementById('addUserPassword').value;
    const role = document.getElementById('addUserRole').value;
    
    if (!username || !password) {
        showStatus('请填写完整信息', 'warning');
        return;
    }
    
    // 验证用户名格式
    if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{1,16}$/.test(username)) {
        showStatus('用户名格式不正确', 'warning');
        return;
    }
    
    // 验证密码格式
    if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,16}$/.test(password)) {
        showStatus('密码格式不正确', 'warning');
        return;
    }
    
    const submitBtn = document.querySelector('#addUserModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>添加中...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/v1/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password,
                role: role
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(`用户创建成功：${username}`, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
            modal.hide();
            
            // 重新加载用户列表
            await loadUsers();
            
        } else {
            showStatus('用户创建失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('创建用户失败:', error);
        showStatus('用户创建失败：' + error.message, 'danger');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 显示编辑用户模态框
function showEditUserModal(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) {
        showStatus('用户不存在', 'danger');
        return;
    }
    
    // 填充表单
    document.getElementById('editUserId').value = user.id;
    document.getElementById('editUserUsername').value = user.username;
    document.getElementById('editUserPassword').value = '';
    document.getElementById('editUserRole').value = user.role;
    document.getElementById('editUserActive').checked = user.is_active;
    
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

// 提交编辑用户
async function submitEditUser() {
    const userId = document.getElementById('editUserId').value;
    const username = document.getElementById('editUserUsername').value.trim();
    const password = document.getElementById('editUserPassword').value;
    const role = document.getElementById('editUserRole').value;
    const isActive = document.getElementById('editUserActive').checked;
    
    const requestData = {
        role: role,
        is_active: isActive
    };
    
    if (username) {
        // 验证用户名格式
        if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{1,16}$/.test(username)) {
            showStatus('用户名格式不正确', 'warning');
            return;
        }
        requestData.username = username;
    }
    
    if (password) {
        // 验证密码格式
        if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,16}$/.test(password)) {
            showStatus('密码格式不正确', 'warning');
            return;
        }
        requestData.password = password;
    }
    
    const submitBtn = document.querySelector('#editUserModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>保存中...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(data.message, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
            modal.hide();
            
            // 重新加载用户列表
            await loadUsers();
            
        } else {
            showStatus('用户更新失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('更新用户失败:', error);
        showStatus('用户更新失败：' + error.message, 'danger');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 显示重置密码模态框
function showResetPasswordModal(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) {
        showStatus('用户不存在', 'danger');
        return;
    }
    
    // 填充表单
    document.getElementById('resetPasswordUserId').value = user.id;
    document.getElementById('resetPasswordUsername').value = user.username;
    document.getElementById('resetPasswordNewPassword').value = '';
    document.getElementById('resetPasswordConfirmPassword').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('resetPasswordModal'));
    modal.show();
}

// 提交重置密码
async function submitResetPassword() {
    const userId = document.getElementById('resetPasswordUserId').value;
    const newPassword = document.getElementById('resetPasswordNewPassword').value;
    const confirmPassword = document.getElementById('resetPasswordConfirmPassword').value;
    
    if (!newPassword || !confirmPassword) {
        showStatus('请填写完整密码信息', 'warning');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        showStatus('两次输入的密码不一致', 'warning');
        return;
    }
    
    // 验证密码格式
    if (!/^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{}|;:,.<>?]{4,16}$/.test(newPassword)) {
        showStatus('密码格式不正确', 'warning');
        return;
    }
    
    const submitBtn = document.querySelector('#resetPasswordModal .btn-warning');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>重置中...';
    submitBtn.disabled = true;
    
    try {
        const formData = new FormData();
        formData.append('password', newPassword);
        
        const response = await fetch(`/api/v1/users/${userId}/reset-password`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(data.message, 'success');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('resetPasswordModal'));
            modal.hide();
            
        } else {
            showStatus('密码重置失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('重置密码失败:', error);
        showStatus('密码重置失败：' + error.message, 'danger');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// 确认删除用户
function confirmDeleteUser(userId) {
    const user = allUsers.find(u => u.id === userId);
    if (!user) {
        showStatus('用户不存在', 'danger');
        return;
    }
    
    if (confirm(`确定要删除用户 "${user.username}" 吗？此操作不可撤销！`)) {
        deleteUser(userId);
    }
}

// 删除用户
async function deleteUser(userId) {
    try {
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(data.message, 'success');
            
            // 重新加载用户列表
            await loadUsers();
            
        } else {
            showStatus('用户删除失败：' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('删除用户失败:', error);
        showStatus('用户删除失败：' + error.message, 'danger');
    }
}