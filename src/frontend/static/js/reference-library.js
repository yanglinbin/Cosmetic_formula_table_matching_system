// 使用共享组件的变量
let currentView = 'card';
let formulas = [];
let currentFormulaId = null;
let formulaUploadHandler;

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function () {
    initializeReferenceLibraryPage();
});

// 初始化配方库管理页面
async function initializeReferenceLibraryPage() {
    // 使用共享组件初始化上传表单
    formulaUploadHandler = new FormulaUploadHandler();
    await formulaUploadHandler.initializeUploadForm({
        // 添加配方时的配置
        categorySelectId: 'addProductCategory',
        subcategorySelectId: 'addProductSubcategory',
        finalProductTypeId: 'addFinalProductType',
        fileInputId: 'addFormulaFile',
        nameInputId: 'addFormulaName',
        customerInputId: 'addCustomerInput',
        customerSuggestionsId: 'addCustomerSuggestions',
        customerDropdownBtnId: 'addCustomerDropdownBtn',
        confirmNameChange: false,
        onProductTypeRecognized: (formulaName) => {
            console.log(`产品类型识别成功: ${formulaName}`);
            // 可以在这里添加更多的处理逻辑
        }
    });
    
    // 加载页面特定数据
    loadStats();
    loadFormulas();
    setupEventListeners();
    // 设置默认视图为卡片视图
    toggleView('card');
    // 设置文件上传时自动填充配方名称
    setupFileUploadListener();
}

// 设置事件监听器
function setupEventListeners() {
    document.getElementById('searchInput').addEventListener('input', filterFormulas);
    document.getElementById('productTypeFilter').addEventListener('change', filterFormulas);
    document.getElementById('customerFilter').addEventListener('change', filterFormulas);
    document.getElementById('sortBy').addEventListener('change', sortFormulas);
}

// 设置文件上传监听器 - 使用共享组件
function setupFileUploadListener() {
    // 添加配方时的文件选择监听器已在initializeReferenceLibraryPage中处理
    
    // 编辑配方时的文件选择监听器
    FileUploadHandler.setupFileUploadListener('editFormulaFile', 'editFormulaName', true);
}

// 加载统计数据
function loadStats() {
    fetch('/api/v1/reference-library-stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('total-formulas').textContent = data.total_formulas || 0;
            document.getElementById('total-ingredients').textContent = data.total_ingredients || 0;
            document.getElementById('product-types').textContent = data.product_types || 0;
            document.getElementById('total-customers').textContent = data.customers || 0;
            document.getElementById('last-updated').textContent = data.last_updated || '无';

            // 更新产品类型筛选器
            const typeFilter = document.getElementById('productTypeFilter');
            typeFilter.innerHTML = '<option value="">📋 所有产品类型</option>';
            if (data.product_type_list) {
                data.product_type_list.forEach(type => {
                    typeFilter.innerHTML += `<option value="${type}">${type}</option>`;
                });
            }

            // 更新客户筛选器
            const customerFilter = document.getElementById('customerFilter');
            customerFilter.innerHTML = '<option value="">👥 所有客户</option>';
            if (data.customer_list) {
                data.customer_list.forEach(customer => {
                    customerFilter.innerHTML += `<option value="${customer}">${customer}</option>`;
                });
            }
        })
        .catch(error => console.error('加载统计数据失败:', error));
}

// 加载配方列表
function loadFormulas() {
    fetch('/api/v1/reference-formulas')
        .then(response => response.json())
        .then(data => {
            formulas = data;
            displayFormulas(formulas);
        })
        .catch(error => {
            console.error('加载配方列表失败:', error);
            showAlert('danger', '加载配方列表失败');
        });
}

// 显示配方列表
function displayFormulas(formulaList) {
    if (currentView === 'card') {
        displayFormulaCards(formulaList);
    } else {
        displayFormulaTable(formulaList);
    }
}

// 显示卡片视图（横向平铺）
function displayFormulaCards(formulaList) {
    const container = document.getElementById('formulasCardView');
    const rowContainer = container.querySelector('.row');

    if (formulaList.length === 0) {
        rowContainer.innerHTML = '<div class="col-12 text-center text-muted"><p>暂无配方数据</p></div>';
        return;
    }

    let html = '';
    formulaList.forEach(formula => {
        html += `
                             <div class="col-xl-3 col-lg-4 col-md-6 col-sm-12">
                                 <div class="card formula-card card-hover h-100">
                                     <div class="card-body">
                                         <h6 class="card-title text-truncate" title="${formula.formula_name}">${formula.formula_name}</h6>
                                         <p class="card-text">
                                             <small class="text-muted">
                                                 <i class="fas fa-tag"></i> ${formula.product_type || '未分类'}
                                             </small><br>
                                             <small class="text-muted">
                                                 <i class="fas fa-vial"></i> ${formula.ingredients_count || 0} 个成分
                                             </small><br>
                                             <small class="text-muted">
                                                 <i class="fas fa-user"></i> ${formula.customer || '无'}
                                             </small><br>
                                             <small class="text-muted">
                                                 <i class="fas fa-upload"></i> ${formula.uploader || '未知'}
                                             </small>
                                         </p>
                                         <div class="d-flex justify-content-center mt-auto">
                                             <div class="action-buttons">
                                                 <button class="btn btn-sm btn-outline-primary" 
                                                         onclick="viewFormula(${formula.id})" title="查看">
                                                     <i class="fas fa-eye"></i>
                                                 </button>
                                                 ${formula.can_edit ? `
                                                 <button class="btn btn-sm btn-outline-warning" 
                                                         onclick="editFormula(${formula.id})" title="编辑">
                                                     <i class="fas fa-edit"></i>
                                                 </button>
                                                 <button class="btn btn-sm btn-outline-danger" 
                                                         onclick="confirmDelete(${formula.id})" title="删除">
                                                     <i class="fas fa-trash"></i>
                                                 </button>` : ''}
                                             </div>
                                         </div>
                                     </div>
                                 </div>
                             </div>
                         `;
    });
    rowContainer.innerHTML = html;
}

// 显示表格视图
function displayFormulaTable(formulaList) {
    const tbody = document.getElementById('formulasTableBody');
    if (formulaList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">暂无配方数据</td></tr>';
        return;
    }

    let html = '';
    formulaList.forEach(formula => {
        html += `
                            <tr>
                                 <td>${formula.id}</td>
                                 <td style="line-height: 1.2; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${formula.formula_name}">${formula.formula_name}</td>
                                 <td style="line-height: 2; max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${formula.product_type || '未分类'}">${formula.product_type || '未分类'}</td>
                                 <td style="white-space: nowrap;">${formula.ingredients_count || 0}</td>
                                 <td style="max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${formula.customer || '无'}">${formula.customer || '无'}</td>
                                 <td><span class="badge bg-secondary">${formula.uploader || '未知'}</span></td>
                                 <td>${new Date(formula.updated_at).toLocaleDateString()}</td>
                                 <td style="white-space: nowrap; min-width: 120px;">
                                     <div class="btn-group" role="group">
                                         <button class="btn btn-sm btn-outline-primary" onclick="viewFormula(${formula.id})" title="查看详情">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                         ${formula.can_edit ? `
                                         <button class="btn btn-sm btn-outline-warning" onclick="editFormula(${formula.id})" title="编辑">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                         <button class="btn btn-sm btn-outline-danger" onclick="confirmDelete(${formula.id})" title="删除">
                                            <i class="fas fa-trash"></i>
                                         </button>` : ''}
                                     </div>
                                </td>
                            </tr>
                        `;
    });
    tbody.innerHTML = html;
}

// 切换视图
function toggleView(view) {
    currentView = view;
    const cardView = document.getElementById('formulasCardView');
    const tableView = document.getElementById('formulasTableView');
    const cardViewBtn = document.getElementById('cardViewBtn');
    const tableViewBtn = document.getElementById('tableViewBtn');

    if (view === 'card') {
        // 显示卡片视图（横向平铺）
        cardView.style.display = 'block';
        tableView.style.display = 'none';
        cardViewBtn.classList.add('active');
        tableViewBtn.classList.remove('active');
    } else {
        // 显示表格视图（纵向平铺）
        cardView.style.display = 'none';
        tableView.style.display = 'block';
        cardViewBtn.classList.remove('active');
        tableViewBtn.classList.add('active');
    }

    displayFormulas(formulas);
}

// 筛选配方
function filterFormulas() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const productType = document.getElementById('productTypeFilter').value;
    const customer = document.getElementById('customerFilter').value;

    let filtered = formulas.filter(formula => {
        const nameMatch = formula.formula_name.toLowerCase().includes(searchTerm);
        const typeMatch = !productType || formula.product_type === productType;
        const customerMatch = !customer || formula.customer === customer;
        return nameMatch && typeMatch && customerMatch;
    });

    displayFormulas(filtered);
}

// 排序配方
function sortFormulas() {
    const sortBy = document.getElementById('sortBy').value;

    formulas.sort((a, b) => {
        if (sortBy === 'formula_name') {
            return a.formula_name.localeCompare(b.formula_name);
        } else if (sortBy === 'ingredients_count') {
            return (b.ingredients_count || 0) - (a.ingredients_count || 0);
        } else {
            return new Date(b.updated_at) - new Date(a.updated_at);
        }
    });

    filterFormulas();
}

// 清除筛选
function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('productTypeFilter').value = '';
    document.getElementById('customerFilter').value = '';
    document.getElementById('sortBy').value = 'updated_at';
    displayFormulas(formulas);
}

// 显示添加配方模态框
function showAddFormulaModal() {
    const modal = new bootstrap.Modal(document.getElementById('addFormulaModal'));
    modal.show();
}

// 产品类型配置加载由共享组件处理
// 移除重复代码

// 填充产品大类选择器 - 使用共享组件
// 由FormulaUploadHandler自动处理

// 更新子分类选择器 - 使用共享组件
function updateAddSubcategories() {
    if (formulaUploadHandler && formulaUploadHandler.productTypeManager) {
        formulaUploadHandler.productTypeManager.updateSubcategories(
            'addProductCategory',
            'addProductSubcategory',
            'addFinalProductType'
        );
    }
}

// 手动识别产品类型（添加配方模态框）
function manualRecognizeAddProductType() {
    const formulaNameInput = document.getElementById('addFormulaName');
    const formulaName = formulaNameInput.value.trim();
    
    if (!formulaName) {
        showAlert('warning', '请先输入配方名称');
        return;
    }
    
    if (formulaUploadHandler && formulaUploadHandler.manualRecognizeProductType) {
        const recognized = formulaUploadHandler.manualRecognizeProductType(
            formulaName,
            'addProductCategory',
            'addProductSubcategory', 
            'addFinalProductType'
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

// 填充编辑模态框的产品大类选择器 - 使用共享组件
function populateEditProductCategories() {
    try {
        console.log('初始化编辑产品类型选择器'); // 调试信息
        if (formulaUploadHandler && formulaUploadHandler.productTypeManager) {
            formulaUploadHandler.productTypeManager.populateProductCategories('editProductCategory');
            console.log('产品类型选择器初始化成功'); // 调试信息
        } else {
            console.warn('formulaUploadHandler 或 productTypeManager 未初始化，跳过产品类型选择器填充');
            // 可以在这里添加备用的产品类型选择器填充逻辑
        }
    } catch (error) {
        console.error('填充产品类型选择器失败:', error);
        // 不抛出错误，避免阻止编辑模态框显示
    }
}

// 更新编辑模态框的子分类选择器 - 使用共享组件
function updateEditSubcategories() {
    if (formulaUploadHandler && formulaUploadHandler.productTypeManager) {
        formulaUploadHandler.productTypeManager.updateSubcategories(
            'editProductCategory',
            'editProductSubcategory',
            'editFinalProductType'
        );
    }
}

// 设置编辑模态框的产品类型值 - 使用共享组件
function setEditProductType(productType) {
    try {
        console.log('设置产品类型:', productType); // 调试信息
        if (formulaUploadHandler && formulaUploadHandler.productTypeManager) {
            formulaUploadHandler.productTypeManager.setProductType(
                'editProductCategory',
                'editProductSubcategory', 
                productType
            );
            console.log('产品类型设置成功'); // 调试信息
        } else {
            console.warn('formulaUploadHandler 或 productTypeManager 未初始化');
            // 如果共享组件未初始化，尝试手动设置
            const categorySelect = document.getElementById('editProductCategory');
            const subcategorySelect = document.getElementById('editProductSubcategory');
            if (categorySelect && subcategorySelect) {
                // 简单的产品类型设置逻辑
                categorySelect.value = productType || '';
                subcategorySelect.value = '';
                console.log('使用备用方法设置产品类型');
            }
        }
    } catch (error) {
        console.error('设置产品类型失败:', error);
        // 不抛出错误，避免阻止编辑模态框显示
    }
}

// 文件选择时自动填充配方名称 - 使用共享组件
// 已在initializeReferenceLibraryPage中处理

// 提交添加配方 - 使用共享组件
async function submitAddFormula() {
    if (formulaUploadHandler) {
        await formulaUploadHandler.submitUploadForm('addFormulaForm', {
            modalId: 'addFormulaModal',
            targetLibrary: 'reference',
            successCallback: (result) => {
                // 重新加载列表和统计
                loadFormulas();
                loadStats();
            }
        });
    }
}

// 查看配方详情
function viewFormula(formulaId) {
    currentFormulaId = formulaId;
    // 使用统一的配方详情API
    fetch(`/api/v1/formula-detail/${formulaId}?formula_type=reference`)
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
            console.error('加载配方详情失败:', error);
            showAlert('danger', '加载配方详情失败: ' + error.message);
        });
}


// 确认删除
function confirmDelete(formulaId) {
    if (confirm('确定要删除这个配方吗？此操作不可撤销。')) {
        deleteFormulaById(formulaId);
    }
}

// 删除配方
function deleteFormulaById(formulaId) {
    fetch(`/api/v1/reference-formulas/${formulaId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showAlert('success', '配方删除成功！');
                loadFormulas();
                loadStats();
            } else {
                showAlert('danger', '删除失败: ' + (data.message || data.detail || '未知错误'));
            }
        })
        .catch(error => {
            console.error('删除配方失败:', error);
            showAlert('danger', '删除配方失败: ' + error.message);
        });
}


// 编辑配方功能
function editFormula(formulaId) {
    if (formulaId) {
        currentFormulaId = formulaId;
    }
    showEditModal();
}

// 显示编辑模态框
function showEditModal() {
    if (!currentFormulaId) {
        showAlert('warning', '请先选择要编辑的配方');
        return;
    }

    // 首先填充产品类型选择器
    populateEditProductCategories();

    // 获取配方详情并填充表单
    fetch(`/api/v1/reference-formulas/${currentFormulaId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('配方详情数据:', data); // 添加调试信息
            
            try {
                // 填充基本表单数据
                document.getElementById('editFormulaId').value = currentFormulaId;
                document.getElementById('editFormulaName').value = data.formula_name || '';
                document.getElementById('editCustomer').value = data.customer || '';

                console.log('基本表单数据填充成功'); // 调试信息

                // 设置产品类型（使用新的二级菜单）
                setEditProductType(data.product_type || '');

                // 清空文件选择
                const fileInput = document.getElementById('editFormulaFile');
                if (fileInput) {
                    fileInput.value = '';
                }

                console.log('准备显示编辑模态框'); // 调试信息

                // 显示编辑模态框
                const editModal = new bootstrap.Modal(document.getElementById('editFormulaModal'));
                editModal.show();
                
                console.log('编辑模态框已显示'); // 调试信息
                
            } catch (error) {
                console.error('填充编辑表单时出错:', error);
                showAlert('danger', `编辑表单初始化失败: ${error.message}`);
            }
        })
        .catch(error => {
            console.error('获取配方详情失败:', error);
            showAlert('danger', `获取配方详情失败: ${error.message}`);
        });
}

// 提交编辑配方
function submitEditFormula() {
    const form = document.getElementById('editFormulaForm');
    const formData = new FormData(form);

    // 添加配方ID到FormData
    formData.append('formula_id', currentFormulaId);

    fetch(`/api/v1/reference-formulas/${currentFormulaId}`, {
        method: 'PUT',
        body: formData
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.detail || err.message || `HTTP ${response.status}: ${response.statusText}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showAlert('success', data.message || '配方编辑成功！');

                // 关闭模态框
                bootstrap.Modal.getInstance(document.getElementById('editFormulaModal')).hide();

                // 如果详情模态框还开着，也关闭它
                const detailModal = bootstrap.Modal.getInstance(document.getElementById('formulaDetailModal'));
                if (detailModal) {
                    detailModal.hide();
                }

                // 刷新数据
                loadFormulas();
                loadStats();
            } else {
                showAlert('danger', '编辑失败: ' + (data.message || data.detail || '未知错误'));
            }
        })
        .catch(error => {
            console.error('编辑配方失败:', error);
            showAlert('danger', '编辑失败: ' + error.message);
        });
}

// 从详情页面确认删除
function confirmDeleteFromDetail() {
    if (confirm('确定要删除这个配方吗？此操作不可撤销。')) {
        deleteFormulaById(currentFormulaId);

        // 关闭详情模态框
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('formulaDetailModal'));
        if (detailModal) {
            detailModal.hide();
        }
    }
}


// 显示批量导入模态框
function showImportModal() {
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    modal.show();

    // 重置表单
    document.getElementById('importForm').reset();
    document.getElementById('importPreview').style.display = 'none';
    document.getElementById('importProgress').style.display = 'none';
    document.getElementById('previewImportBtn').disabled = true;
    document.getElementById('startImportBtn').disabled = true;
}

// 监听文件夹选择
document.addEventListener('DOMContentLoaded', function () {
    const folderInput = document.getElementById('importFolder');
    if (folderInput) {
        folderInput.addEventListener('change', function (e) {
            if (e.target.files && e.target.files.length > 0) {
                document.getElementById('previewImportBtn').disabled = false;
            } else {
                document.getElementById('previewImportBtn').disabled = true;
                document.getElementById('startImportBtn').disabled = true;
            }
        });
    }
});

// 预览导入
function previewImport() {
    const folderInput = document.getElementById('importFolder');
    const files = folderInput.files;

    if (!files || files.length === 0) {
        showAlert('warning', '请先选择文件夹');
        return;
    }

    document.getElementById('importPreviewContent').innerHTML = '';

    // 解析文件夹结构
    const structure = analyzeFolderStructure(files);

    displayImportPreview(structure);

    document.getElementById('importPreview').style.display = 'block';
    document.getElementById('startImportBtn').disabled = false;
}


// 解析文件夹结构
function analyzeFolderStructure(files) {
    const structure = {};
    const excelFiles = [];

    for (let file of files) {
        const path = file.webkitRelativePath;
        const fileName = file.name;

        // 只处理Excel文件
        if (fileName.toLowerCase().endsWith('.xlsx') || fileName.toLowerCase().endsWith('.xls')) {
            const pathParts = path.split('/');

            if (pathParts.length >= 4) {
                // 主文件夹/客户/产品大类/产品小类/文件.xlsx
                const customer = pathParts[1] || '未知客户';
                let productCategory = pathParts[2] || '其他类';
                let productSubcategory = pathParts[3] || '';

                // 处理文件夹名中的特殊字符
                productCategory = processFolderName(productCategory);
                productSubcategory = processFolderName(productSubcategory);

                // 获取文件名（不带扩展名）
                const formulaName = removeFileExtension(fileName);

                const formulaInfo = {
                    file: file,
                    fileName: fileName,
                    formulaName: formulaName,  // 添加去除扩展名的配方名称
                    customer: customer,
                    productType: productSubcategory ? `${productCategory}-${productSubcategory}` : productCategory,
                    path: path
                };

                if (!structure[customer]) {
                    structure[customer] = {};
                }
                if (!structure[customer][formulaInfo.productType]) {
                    structure[customer][formulaInfo.productType] = [];
                }
                structure[customer][formulaInfo.productType].push(formulaInfo);
                excelFiles.push(formulaInfo);
            }
        }
    }

    return {structure, excelFiles};
}

function processFolderName(folderName) {
    // 处理文件夹名中的特殊字符，去除多余空格等
    if (!folderName) return folderName;
    
    return folderName.trim()
        .replace(/\s+/g, ' ')  // 将多个空格替换为单个空格
        .replace(/['"]/g, '')  // 移除引号
        .replace(/[<>:"|?*]/g, '');  // 移除Windows文件系统不允许的字符
}

function removeFileExtension(filename) {
    // 处理没有扩展名的情况
    if (!filename.includes('.')) return filename;

    // 处理以点开头的文件名
    if (filename.startsWith('.')) {
        return filename.substring(1).split('.').slice(0, -1).join('.');
    }

    // 常规处理：移除最后一个点之后的部分
    return filename.substring(0, filename.lastIndexOf('.'));
}


// 显示导入预览
function displayImportPreview({structure, excelFiles}) {
    const previewContent = document.getElementById('importPreviewContent');

    // 清空预览内容
    previewContent.innerHTML = '';

    // 创建主容器
    const container = document.createElement('div');
    container.className = 'mb-3';

    // 添加文件计数
    const countElement = document.createElement('strong');
    countElement.textContent = `发现 ${excelFiles.length} 个配方文件：`;
    container.appendChild(countElement);

    previewContent.appendChild(container);

    // 遍历每个客户
    for (const [customer, productTypes] of Object.entries(structure)) {
        const customerDiv = document.createElement('div');
        customerDiv.className = 'mb-3';

        const customerHeader = document.createElement('h6');
        customerHeader.className = 'text-primary';
        customerHeader.innerHTML = `👤 客户: ${customer}`;
        customerDiv.appendChild(customerHeader);

        // 遍历每个产品类型
        for (const [productType, files] of Object.entries(productTypes)) {
            const productDiv = document.createElement('div');
            productDiv.className = 'ms-3 mb-2';

            const productHeader = document.createElement('strong');
            productHeader.innerHTML = `📦 产品类型: ${productType} (${files.length} 个文件)`;
            productDiv.appendChild(productHeader);

            const fileList = document.createElement('ul');
            fileList.className = 'ms-3 small';

            // 添加每个文件
            files.forEach(fileInfo => {
                const listItem = document.createElement('li');

                // 创建文本节点而不是设置innerHTML
                const formulaText = document.createTextNode('配方：');
                const formulaNameText = document.createTextNode(fileInfo.formulaName);

                listItem.appendChild(formulaText);
                listItem.appendChild(formulaNameText);
                fileList.appendChild(listItem);
            });

            productDiv.appendChild(fileList);
            customerDiv.appendChild(productDiv);
        }

        previewContent.appendChild(customerDiv);
    }
}



// 开始批量导入
async function startBatchImport() {
    const folderInput = document.getElementById('importFolder');
    const files = folderInput.files;

    if (!files || files.length === 0) {
        showAlert('warning', '请先选择文件夹');
        return;
    }

    const {structure, excelFiles} = analyzeFolderStructure(files);

    if (excelFiles.length === 0) {
        showAlert('warning', '未找到有效的Excel文件');
        return;
    }

    // 显示进度条
    document.getElementById('importProgress').style.display = 'block';
    document.getElementById('startImportBtn').disabled = true;

    const progressBar = document.querySelector('#importProgress .progress-bar');
    const statusDiv = document.getElementById('importStatus');

    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < excelFiles.length; i++) {
        const fileInfo = excelFiles[i];
        const progress = ((i + 1) / excelFiles.length) * 100;

        progressBar.style.width = `${progress}%`;
        statusDiv.textContent = `正在导入: ${fileInfo.formulaName} (${i + 1}/${excelFiles.length})`;

        try {
            await importSingleFile(fileInfo);
            successCount++;
        } catch (error) {
            console.error(`导入文件失败: ${fileInfo.formulaName}`, error);
            errorCount++;
        }

        // 添加短暂延迟，避免过快的请求
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    statusDiv.innerHTML = `
                        导入完成！成功: ${successCount} 个，失败: ${errorCount} 个
                        <br><small class="text-muted">页面将在3秒后自动刷新</small>
                    `;

    // 3秒后关闭模态框并刷新页面
    setTimeout(() => {
        bootstrap.Modal.getInstance(document.getElementById('importModal')).hide();
        // 刷新页面以显示最新数据
        window.location.reload();
    }, 3000);
}

// 导入单个文件
async function importSingleFile(fileInfo) {
    const formData = new FormData();
    formData.append('file', fileInfo.file);
    formData.append('formula_name', fileInfo.formulaName);  // 使用已经去除扩展名的配方名称
    formData.append('customer', fileInfo.customer);
    formData.append('product_type', fileInfo.productType);
    formData.append('target_library', 'reference');

    const response = await fetch('/api/v1/upload-formula', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();

    if (!response.ok) {
        // 处理HTTP错误，包括400(同名冲突)等
        throw new Error(data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    if (!data.success) {
        throw new Error(data.message || data.detail || '未知错误');
    }

    return data;
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
                                    <table class="table table-striped table-hover table-sm">
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
        const ingredientContentDisplay = item.ingredient_content === '-' ? '-' : `${item.ingredient_content}%`;
        const actualContentDisplay = item.actual_component_content === '-' ? '-' : `${item.actual_component_content}%`;

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
                                text-indent: 0rem;
                                padding-right: 1rem;
                            }
                            .compound-component td:nth-child(2) {
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
                                            <i class="fas fa-eye"></i> 配方详情 - ${data.formula_name}
                                        </h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body">
                                        ${detailContent}
                                    </div>
                                    <div class="modal-footer">
                                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                            <i class="fas fa-times"></i> 关闭
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

    // 添加到页面
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // 显示模态框
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();

    // 监听模态框关闭事件，关闭后删除DOM元素
    document.getElementById(modalId).addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
}

// 显示提示消息 - 使用共享组件
// showAlert 已在common.js中定义，可直接使用

// 表格排序功能
let currentSortField = null;
let currentSortOrder = 'asc';

function sortTable(field) {
    // 如果点击的是同一个字段，则切换排序顺序
    if (currentSortField === field) {
        currentSortOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortField = field;
        currentSortOrder = 'asc';
    }
    
    // 更新排序图标
    updateSortIcons(field, currentSortOrder);
    
    // 对配方数据进行排序
    const sortedFormulas = [...formulas].sort((a, b) => {
        let valueA = a[field] || '';
        let valueB = b[field] || '';
        
        // 处理空值
        if (!valueA && !valueB) return 0;
        if (!valueA) return currentSortOrder === 'asc' ? 1 : -1;
        if (!valueB) return currentSortOrder === 'asc' ? -1 : 1;
        
        // 字符串比较
        valueA = valueA.toString().toLowerCase();
        valueB = valueB.toString().toLowerCase();
        
        const result = valueA.localeCompare(valueB);
        return currentSortOrder === 'asc' ? result : -result;
    });
    
    // 重新显示表格
    displayFormulaTable(sortedFormulas);
}

function updateSortIcons(activeField, order) {
    // 重置所有排序图标
    const sortIcons = document.querySelectorAll('th .fa-sort, th .fa-sort-up, th .fa-sort-down');
    sortIcons.forEach(icon => {
        icon.className = 'fas fa-sort text-muted';
    });
    
    // 更新当前激活字段的图标
    const activeButton = document.querySelector(`th button[onclick="sortTable('${activeField}')"] i`);
    if (activeButton) {
        activeButton.className = order === 'asc' ? 'fas fa-sort-up text-primary' : 'fas fa-sort-down text-primary';
    }
}

// 登出功能在common.js中已定义
// 移除重复代码

// 显示快速映射模态框
async function showQuickMappingModal(context = 'add') {
    const formulaNameInput = document.getElementById(context === 'add' ? 'addFormulaName' : 'formulaName');
    const formulaName = formulaNameInput ? formulaNameInput.value.trim() : '';
    
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
async function submitQuickMapping(context = 'add') {
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
            const currentFormulaName = document.getElementById(context === 'add' ? 'addFormulaName' : 'formulaName').value.trim();
            if (currentFormulaName && (currentFormulaName.includes(fromName) || fromName.includes(currentFormulaName))) {
                setTimeout(() => {
                    if (context === 'add') {
                        manualRecognizeAddProductType();
                    } else {
                        manualRecognizeProductType();
                    }
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
