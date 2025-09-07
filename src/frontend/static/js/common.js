// =============================================
// 共享的配方上传组件 - common.js
// 基于upload-match页面的功能实现，供两个页面共享使用
// =============================================

// =============================================
// 1. 产品类型配置管理器
// =============================================
class ProductTypeManager {
    constructor() {
        this.productTypesConfig = {};
    }

    // 加载产品类型配置
    async loadProductTypes() {
        try {
            const response = await fetch('/api/v1/config/product-types');
            const data = await response.json();
            if (data.success) {
                this.productTypesConfig = data.data;
                return this.productTypesConfig;
            }
        } catch (error) {
            console.error('加载产品类型配置失败:', error);
            // 使用默认配置
            this.productTypesConfig = {
                '驻留类': ['护肤水', '护肤霜膏乳', '涂抹面膜', '片状面膜', '凝胶', '护肤精油', '护发精油'],
                '淋洗类': ['洗发水', '护发素', '沐浴露', '洗面霜膏乳', '洗面慕斯', '卸妆霜膏乳', '卸妆油', '卸妆水'],
                '其他类': []
            };
            return this.productTypesConfig;
        }
    }

    // 填充产品大类选择器
    populateProductCategories(selectElementId) {
        const categorySelect = document.getElementById(selectElementId);
        if (!categorySelect) return;

        categorySelect.innerHTML = '<option value="">请选择产品大类</option>';

        for (const category in this.productTypesConfig) {
            const option = document.createElement('option');
            option.value = category;
            option.textContent = category;
            categorySelect.appendChild(option);
        }
    }

    // 更新子分类选择器
    updateSubcategories(categorySelectId, subcategorySelectId, finalProductTypeId) {
        const categorySelect = document.getElementById(categorySelectId);
        const subcategorySelect = document.getElementById(subcategorySelectId);
        const finalProductType = document.getElementById(finalProductTypeId);

        if (!categorySelect || !subcategorySelect || !finalProductType) return;

        const selectedCategory = categorySelect.value;

        // 清空子分类
        subcategorySelect.innerHTML = '';
        finalProductType.value = '';

        if (!selectedCategory) {
            subcategorySelect.disabled = true;
            subcategorySelect.innerHTML = '<option value="">请先选择产品大类</option>';
            return;
        }

        const subcategories = this.productTypesConfig[selectedCategory] || [];

        if (subcategories.length === 0) {
            // 没有子分类，直接使用大类
            subcategorySelect.disabled = true;
            subcategorySelect.innerHTML = '<option value="">无细分类型</option>';
            finalProductType.value = selectedCategory;
        } else {
            // 有子分类，启用选择器
            subcategorySelect.disabled = false;
            subcategorySelect.innerHTML = '<option value="">请选择细分类型</option>';

            subcategories.forEach(subcategory => {
                const option = document.createElement('option');
                option.value = subcategory;
                option.textContent = subcategory;
                subcategorySelect.appendChild(option);
            });

            // 监听子分类选择
            subcategorySelect.onchange = function () {
                if (this.value) {
                    finalProductType.value = `${selectedCategory}-${this.value}`;
                } else {
                    finalProductType.value = '';
                }
            };
        }
    }
}

// =============================================
// 2. 文件名处理工具
// =============================================
class FileNameUtils {
    // 去除文件扩展名
    static removeExtension(fileName) {
        if (!fileName || typeof fileName !== 'string') return '';
        return fileName.replace(/\.[^/.]+$/, "");
    }

    // 获取文件扩展名
    static getExtension(fileName) {
        if (!fileName || typeof fileName !== 'string') return '';
        const matches = fileName.match(/\.([^/.]+)$/);
        return matches ? matches[1].toLowerCase() : '';
    }
}

// =============================================
// 3. 产品类型自动识别器
// =============================================
class ProductTypeRecognizer {
    constructor() {
        this.productTypesConfig = {};
        this.productTypeMappings = {}; // 产品类型映射表
    }

    // 设置产品类型配置
    setProductTypesConfig(config) {
        this.productTypesConfig = config;
    }

    // 设置产品类型映射表
    setProductTypeMappings(mappings) {
        this.productTypeMappings = mappings;
    }

    // 加载产品类型映射表
    async loadProductTypeMappings() {
        try {
            const response = await fetch('/api/v1/config/product-type-mappings');
            const data = await response.json();
            if (data.success) {
                this.productTypeMappings = data.data || {};
                return this.productTypeMappings;
            }
        } catch (error) {
            console.error('加载产品类型映射表失败:', error);
        }
        return {};
    }

    // 从配方名称自动识别产品类型
    recognizeProductType(formulaName) {
        if (!formulaName || typeof formulaName !== 'string') {
            return { category: '', subcategory: '', fullType: '', matchedBy: '' };
        }

        const cleanFormulaName = formulaName.trim();

        // 第一步：检查映射表（精确匹配和模糊匹配）
        const mappingResult = this.checkMappings(cleanFormulaName);
        if (mappingResult.category) {
            return { ...mappingResult, matchedBy: 'mapping' };
        }

        // 第二步：使用整体产品名进行关键词匹配
        const keywordResult = this.matchByKeywords(cleanFormulaName);
        if (keywordResult.category) {
            return { ...keywordResult, matchedBy: 'keyword' };
        }

        // 没有匹配到任何类型
        return { category: '', subcategory: '', fullType: '', matchedBy: '' };
    }

    // 检查映射表
    checkMappings(formulaName) {
        // 1. 精确匹配
        if (this.productTypeMappings[formulaName]) {
            return this.parseProductType(this.productTypeMappings[formulaName]);
        }

        // 2. 模糊匹配：检查配方名是否包含映射表中的关键词
        for (const [mappingKey, mappingValue] of Object.entries(this.productTypeMappings)) {
            if (formulaName.includes(mappingKey) || mappingKey.includes(formulaName)) {
                return this.parseProductType(mappingValue);
            }
        }

        return { category: '', subcategory: '', fullType: '' };
    }

    // 通过关键词匹配（使用整体产品名）
    matchByKeywords(formulaName) {
        // 遍历所有产品类型配置进行匹配
        for (const [category, subcategories] of Object.entries(this.productTypesConfig)) {
            // 匹配子分类
            for (const subcategory of subcategories) {
                if (formulaName.includes(subcategory)) {
                    return {
                        category: category,
                        subcategory: subcategory,
                        fullType: `${category}-${subcategory}`
                    };
                }
            }
            
            // 如果没有子分类，直接匹配大类名
            if (subcategories.length === 0 && formulaName.includes(category)) {
                return {
                    category: category,
                    subcategory: '',
                    fullType: category
                };
            }
        }

        return { category: '', subcategory: '', fullType: '' };
    }

    // 解析产品类型字符串
    parseProductType(productTypeString) {
        if (!productTypeString || typeof productTypeString !== 'string') {
            return { category: '', subcategory: '', fullType: '' };
        }

        // 解析格式：大类-小类 或 大类
        const parts = productTypeString.split('-');
        const category = parts[0] || '';
        const subcategory = parts[1] || '';
        
        return {
            category: category,
            subcategory: subcategory,
            fullType: subcategory ? `${category}-${subcategory}` : category
        };
    }

    // 添加产品类型映射
    async addProductTypeMapping(fromName, toProductType) {
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
                // 更新本地映射表
                this.productTypeMappings[fromName] = toProductType;
                return true;
            }
        } catch (error) {
            console.error('添加产品类型映射失败:', error);
        }
        return false;
    }

    // 删除产品类型映射
    async deleteProductTypeMapping(fromName) {
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
                // 更新本地映射表
                delete this.productTypeMappings[fromName];
                return true;
            }
        } catch (error) {
            console.error('删除产品类型映射失败:', error);
        }
        return false;
    }

    // 获取所有产品类型映射
    getProductTypeMappings() {
        return this.productTypeMappings;
    }

    // 动态填充产品类型下拉菜单
    async populateProductTypeDropdown(selectId) {
        try {
            const select = document.getElementById(selectId);
            if (!select) {
                console.error(`找不到下拉菜单元素: ${selectId}`);
                return;
            }

            // 清空现有选项（保留第一个占位选项）
            select.innerHTML = '<option value="">请选择目标产品类型</option>';

            // 获取产品类型配置
            if (!this.productTypesConfig || Object.keys(this.productTypesConfig).length === 0) {
                await this.loadProductTypesConfig();
            }

            // 填充选项
            Object.entries(this.productTypesConfig).forEach(([category, subcategories]) => {
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
            console.error('填充产品类型下拉菜单失败:', error);
        }
    }

    // 加载产品类型配置
    async loadProductTypesConfig() {
        try {
            const response = await fetch('/api/v1/config/product-types');
            const data = await response.json();
            if (data.success) {
                this.productTypesConfig = data.data || {};
                return this.productTypesConfig;
            }
        } catch (error) {
            console.error('加载产品类型配置失败:', error);
        }
        
        // 返回默认配置
        this.productTypesConfig = {
            '驻留类': ['护肤水', '护肤霜膏乳', '涂抹面膜', '片状面膜', '凝胶', '护肤精油', '护发精油'],
            '淋洗类': ['洗发水', '护发素', '沐浴露', '洗面霜膏乳', '洗面慕斯', '卸妆霜膏乳', '卸妆油', '卸妆水'],
            '其他类': []
        };
        return this.productTypesConfig;
    }

    // 自动设置产品类型到表单
    autoSetProductType(formulaName, categorySelectId, subcategorySelectId, finalProductTypeId, productTypeManager) {
        const recognized = this.recognizeProductType(formulaName);
        
        if (recognized.category && productTypeManager) {
            // 设置大类
            const categorySelect = document.getElementById(categorySelectId);
            if (categorySelect) {
                categorySelect.value = recognized.category;
                
                // 触发子分类更新
                productTypeManager.updateSubcategories(categorySelectId, subcategorySelectId, finalProductTypeId);
                
                // 如果有子分类，设置子分类
                if (recognized.subcategory) {
                    setTimeout(() => {
                        const subcategorySelect = document.getElementById(subcategorySelectId);
                        if (subcategorySelect) {
                            subcategorySelect.value = recognized.subcategory;
                            // 触发change事件更新隐藏字段
                            subcategorySelect.dispatchEvent(new Event('change'));
                        }
                    }, 100);
                }
            }
            
            return true; // 识别成功
        }
        
        return false; // 识别失败
    }
}

// =============================================
// 4. 文件上传处理器
// =============================================
class FileUploadHandler {
    // 设置文件选择时自动填充配方名称和识别产品类型
    static setupFileUploadListener(fileInputId, nameInputId, confirmChange = false, options = {}) {
        const fileInput = document.getElementById(fileInputId);
        const nameInput = document.getElementById(nameInputId);

        if (fileInput && nameInput) {
            fileInput.addEventListener('change', function (e) {
                const file = e.target.files[0];
                if (file) {
                    // 获取文件名（不带扩展名）
                    const fileName = FileNameUtils.removeExtension(file.name);
                    
                    let shouldUpdateName = true;
                    if (confirmChange) {
                        // 编辑模式：只有在配方名称为空或者用户确认时才更新
                        shouldUpdateName = !nameInput.value.trim() || confirm('是否使用文件名作为配方名称？');
                    }
                    
                    if (shouldUpdateName) {
                        nameInput.value = fileName;
                        
                        // 自动识别产品类型（如果提供了相关选项）
                        if (options.autoRecognizeProductType && 
                            options.productTypeRecognizer && 
                            options.productTypeManager) {
                            
                            const recognized = options.productTypeRecognizer.autoSetProductType(
                                fileName,
                                options.categorySelectId,
                                options.subcategorySelectId,
                                options.finalProductTypeId,
                                options.productTypeManager
                            );
                            
                            if (recognized && options.onProductTypeRecognized) {
                                options.onProductTypeRecognized(fileName);
                            }
                        }
                    }
                }
            });
        }
    }
}

// =============================================
// 5. 客户自动完成组件
// =============================================
class CustomerAutocomplete {
    constructor() {
        this.allCustomers = [];
    }

    // 加载客户列表
    async loadCustomers() {
        try {
            const response = await fetch('/api/v1/customers');
            const data = await response.json();
            if (data.success) {
                this.allCustomers = data.customers;
                return this.allCustomers;
            }
        } catch (error) {
            console.error('加载客户列表失败:', error);
        }
        return [];
    }

    // 设置客户输入框功能
    setupCustomerInput(inputId, suggestionsId, dropdownBtnId) {
        const customerInput = document.getElementById(inputId);
        const customerDropdownBtn = document.getElementById(dropdownBtnId);
        const suggestionsContainer = document.getElementById(suggestionsId);
        
        if (!customerInput || !suggestionsContainer) return;
        
        let currentHighlightIndex = -1;
        
        // 过滤并显示匹配的客户
        const filterAndShowCustomers = (searchTerm) => {
            const suggestionsContent = suggestionsContainer.querySelector('.suggestions-content');
            suggestionsContent.innerHTML = '';
            currentHighlightIndex = -1;
            
            if (!searchTerm) {
                suggestionsContent.innerHTML = '<div class="suggestions-empty">开始输入以搜索客户...</div>';
                return;
            }
            
            const filteredCustomers = this.allCustomers.filter(customer => 
                customer.toLowerCase().includes(searchTerm.toLowerCase())
            );
            
            if (filteredCustomers.length === 0) {
                suggestionsContent.innerHTML = '<div class="suggestions-empty">未找到匹配的客户</div>';
            } else {
                filteredCustomers.forEach(customer => {
                    const item = document.createElement('div');
                    item.className = 'suggestion-item';
                    
                    // 高亮匹配的文字
                    const highlightedName = customer.replace(
                        new RegExp(searchTerm, 'gi'),
                        '<mark>$&</mark>'
                    );
                    
                    item.innerHTML = `<i class="fas fa-user"></i>${highlightedName}`;
                    item.addEventListener('click', () => this.selectCustomer(customer, inputId, suggestionsId));
                    suggestionsContent.appendChild(item);
                });
            }
        };

        // 显示所有客户列表
        const showAllCustomers = () => {
            const suggestionsContent = suggestionsContainer.querySelector('.suggestions-content');
            suggestionsContent.innerHTML = '';
            
            if (this.allCustomers.length === 0) {
                suggestionsContent.innerHTML = '<div class="suggestions-empty">暂无客户数据</div>';
                return;
            }
            
            this.allCustomers.forEach(customer => {
                const item = document.createElement('div');
                item.className = 'suggestion-item';
                item.innerHTML = `<i class="fas fa-user"></i>${customer}`;
                item.addEventListener('click', () => this.selectCustomer(customer, inputId, suggestionsId));
                suggestionsContent.appendChild(item);
            });
        };
        
        // 输入框获得焦点时
        customerInput.addEventListener('focus', function() {
            const searchTerm = this.value.trim();
            if (searchTerm) {
                filterAndShowCustomers(searchTerm);
            } else {
                showAllCustomers();
            }
            CustomerAutocomplete.showSuggestions(suggestionsId);
        });
        
        // 输入时实时搜索
        customerInput.addEventListener('input', function() {
            const searchTerm = this.value.trim();
            filterAndShowCustomers(searchTerm);
            
            if (suggestionsContainer.style.display === 'none') {
                CustomerAutocomplete.showSuggestions(suggestionsId);
            }
        });
        
        // 键盘导航支持
        customerInput.addEventListener('keydown', function(event) {
            const suggestionItems = suggestionsContainer.querySelectorAll('.suggestion-item');
            
            switch(event.key) {
                case 'ArrowDown':
                    event.preventDefault();
                    currentHighlightIndex = Math.min(currentHighlightIndex + 1, suggestionItems.length - 1);
                    updateHighlight(suggestionItems);
                    break;
                    
                case 'ArrowUp':
                    event.preventDefault();
                    currentHighlightIndex = Math.max(currentHighlightIndex - 1, -1);
                    updateHighlight(suggestionItems);
                    break;
                    
                case 'Enter':
                    event.preventDefault();
                    if (currentHighlightIndex >= 0 && suggestionItems[currentHighlightIndex]) {
                        const customerName = suggestionItems[currentHighlightIndex].textContent;
                        this.selectCustomer(customerName, inputId, suggestionsId);
                    }
                    break;
                    
                case 'Escape':
                    CustomerAutocomplete.hideSuggestions(suggestionsId);
                    this.blur();
                    break;
            }
        }.bind(this));
        
        // 更新高亮显示
        function updateHighlight(items) {
            items.forEach((item, index) => {
                item.classList.toggle('highlighted', index === currentHighlightIndex);
            });
            
            // 滚动到可见区域
            if (currentHighlightIndex >= 0 && items[currentHighlightIndex]) {
                items[currentHighlightIndex].scrollIntoView({ block: 'nearest' });
            }
        }
        
        // 点击下拉按钮显示所有客户
        if (customerDropdownBtn) {
            customerDropdownBtn.addEventListener('click', function(event) {
                event.preventDefault();
                event.stopPropagation();
                
                if (suggestionsContainer.style.display === 'none') {
                    showAllCustomers();
                    CustomerAutocomplete.showSuggestions(suggestionsId);
                    customerInput.focus();
                } else {
                    CustomerAutocomplete.hideSuggestions(suggestionsId);
                }
            });
        }
        
        // 点击外部区域隐藏建议框
        document.addEventListener('click', function(event) {
            if (!customerInput.contains(event.target) && 
                !suggestionsContainer.contains(event.target) &&
                (!customerDropdownBtn || !customerDropdownBtn.contains(event.target))) {
                CustomerAutocomplete.hideSuggestions(suggestionsId);
            }
        });
        
        // 输入框失去焦点时延迟隐藏（给点击事件时间执行）
        customerInput.addEventListener('blur', function() {
            setTimeout(() => {
                if (!suggestionsContainer.matches(':hover')) {
                    CustomerAutocomplete.hideSuggestions(suggestionsId);
                }
            }, 150);
        });
    }

    // 选择客户
    selectCustomer(customerName, inputId, suggestionsId) {
        const customerInput = document.getElementById(inputId);
        
        if (customerInput) {
            customerInput.value = customerName;
            CustomerAutocomplete.hideSuggestions(suggestionsId);
            customerInput.focus();
        }
    }

    // 显示建议框（静态方法）
    static showSuggestions(suggestionsId) {
        const suggestionsContainer = document.getElementById(suggestionsId);
        if (suggestionsContainer) {
            suggestionsContainer.style.display = 'block';
            suggestionsContainer.classList.remove('hiding');
        }
    }

    // 隐藏建议框（静态方法）
    static hideSuggestions(suggestionsId) {
        const suggestionsContainer = document.getElementById(suggestionsId);
        if (suggestionsContainer) {
            suggestionsContainer.classList.add('hiding');
            
            setTimeout(() => {
                suggestionsContainer.style.display = 'none';
                suggestionsContainer.classList.remove('hiding');
            }, 150);
        }
    }
}

// =============================================
// 6. 全局通知系统
// =============================================
class GlobalNotificationSystem {
    constructor() {
        this.notificationQueue = [];
        this.currentNotification = null;
        this.isShowing = false;
    }

    // 显示通知
    static showNotification(type, message, options = {}) {
        const instance = GlobalNotificationSystem.getInstance();
        instance.addNotification(type, message, options);
    }

    // 获取单例实例
    static getInstance() {
        if (!GlobalNotificationSystem.instance) {
            GlobalNotificationSystem.instance = new GlobalNotificationSystem();
        }
        return GlobalNotificationSystem.instance;
    }

    // 添加通知到队列
    addNotification(type, message, options = {}) {
        const notification = {
            type,
            message,
            duration: options.duration || 4000,
            icon: this.getIcon(type),
            id: Date.now() + Math.random()
        };

        this.notificationQueue.push(notification);
        
        if (!this.isShowing) {
            this.showNext();
        }
    }

    // 显示下一个通知
    showNext() {
        if (this.notificationQueue.length === 0) {
            this.isShowing = false;
            return;
        }

        this.isShowing = true;
        const notification = this.notificationQueue.shift();
        this.currentNotification = notification;

        this.displayNotification(notification);
    }

    // 显示通知
    displayNotification(notification) {
        // 移除现有通知
        this.removeCurrentNotification();

        // 创建通知元素
        const notificationElement = document.createElement('div');
        notificationElement.className = `global-notification alert-${notification.type}`;
        notificationElement.id = `notification-${notification.id}`;
        
        notificationElement.innerHTML = `
            <div class="notification-content">
                <div class="notification-icon">
                    <i class="${notification.icon}"></i>
                </div>
                <div class="notification-message">
                    ${notification.message}
                </div>
                <button type="button" class="btn-close" onclick="GlobalNotificationSystem.getInstance().hideNotification('${notification.id}')"></button>
            </div>
        `;

        // 添加到页面
        document.body.appendChild(notificationElement);

        // 触发显示动画
        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 10);

        // 自动隐藏
        setTimeout(() => {
            this.hideNotification(notification.id);
        }, notification.duration);
    }

    // 隐藏通知
    hideNotification(notificationId) {
        const element = document.getElementById(`notification-${notificationId}`);
        if (element) {
            element.classList.add('hide');
            element.classList.remove('show');
            
            setTimeout(() => {
                if (element.parentNode) {
                    element.remove();
                }
                
                // 显示下一个通知
                setTimeout(() => {
                    this.showNext();
                }, 200);
            }, 400);
        }
    }

    // 移除当前通知
    removeCurrentNotification() {
        const currentElements = document.querySelectorAll('.global-notification');
        currentElements.forEach(element => {
            element.classList.add('hide');
            element.classList.remove('show');
            setTimeout(() => {
                if (element.parentNode) {
                    element.remove();
                }
            }, 400);
        });
    }

    // 获取图标
    getIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            danger: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    // 清空所有通知
    clearAll() {
        this.notificationQueue = [];
        this.removeCurrentNotification();
        this.isShowing = false;
    }
}

// 提示消息系统（保持向后兼容）
class AlertSystem {
    // 显示提示消息
    static showAlert(type, message, options = {}) {
        GlobalNotificationSystem.showNotification(type, message, options);
    }
}

// =============================================
// 7. 通用配方上传表单处理器
// =============================================
class FormulaUploadHandler {
    constructor() {
        this.productTypeManager = new ProductTypeManager();
        this.customerAutocomplete = new CustomerAutocomplete();
        this.productTypeRecognizer = new ProductTypeRecognizer();
    }

    // 初始化上传表单的通用功能
    async initializeUploadForm(options = {}) {
        const defaultOptions = {
            categorySelectId: 'uploadProductCategory',
            subcategorySelectId: 'uploadProductSubcategory', 
            finalProductTypeId: 'uploadFinalProductType',
            fileInputId: 'formulaFile',
            nameInputId: 'formulaName',
            customerInputId: 'customerInput',
            customerSuggestionsId: 'customerSuggestions',
            customerDropdownBtnId: 'customerDropdownBtn',
            confirmNameChange: false,
            autoRecognizeProductType: true, // 默认开启产品类型自动识别
            onProductTypeRecognized: null // 产品类型识别成功后的回调
        };
        
        const config = { ...defaultOptions, ...options };

        // 加载产品类型配置
        await this.productTypeManager.loadProductTypes();
        this.productTypeManager.populateProductCategories(config.categorySelectId);
        
        // 将产品类型配置设置到识别器中
        this.productTypeRecognizer.setProductTypesConfig(this.productTypeManager.productTypesConfig);
        
        // 加载产品类型映射表
        await this.productTypeRecognizer.loadProductTypeMappings();
        
        // 设置文件上传监听器（带产品类型自动识别）
        FileUploadHandler.setupFileUploadListener(
            config.fileInputId, 
            config.nameInputId, 
            config.confirmNameChange,
            {
                autoRecognizeProductType: config.autoRecognizeProductType,
                productTypeRecognizer: this.productTypeRecognizer,
                productTypeManager: this.productTypeManager,
                categorySelectId: config.categorySelectId,
                subcategorySelectId: config.subcategorySelectId,
                finalProductTypeId: config.finalProductTypeId,
                onProductTypeRecognized: config.onProductTypeRecognized
            }
        );

        // 加载客户列表并设置自动完成
        await this.customerAutocomplete.loadCustomers();
        this.customerAutocomplete.setupCustomerInput(
            config.customerInputId,
            config.customerSuggestionsId,
            config.customerDropdownBtnId
        );

        return {
            productTypeManager: this.productTypeManager,
            customerAutocomplete: this.customerAutocomplete,
            productTypeRecognizer: this.productTypeRecognizer
        };
    }

    // 手动触发产品类型识别
    manualRecognizeProductType(formulaName, categorySelectId, subcategorySelectId, finalProductTypeId) {
        if (this.productTypeRecognizer && this.productTypeManager) {
            return this.productTypeRecognizer.autoSetProductType(
                formulaName,
                categorySelectId,
                subcategorySelectId,
                finalProductTypeId,
                this.productTypeManager
            );
        }
        return false;
    }

    // 提交上传表单的通用处理
    async submitUploadForm(formId, options = {}) {
        const defaultOptions = {
            apiEndpoint: '/api/v1/upload-formula',
            modalId: null,
            submitButtonSelector: null,
            successCallback: null,
            errorCallback: null,
            targetLibrary: 'to_match' // 'to_match' 或 'reference'
        };
        
        const config = { ...defaultOptions, ...options };
        
        const form = document.getElementById(formId);
        const formData = new FormData(form);
        
        // 确定提交按钮
        let submitButton = null;
        if (config.submitButtonSelector) {
            submitButton = document.querySelector(config.submitButtonSelector);
        } else if (config.modalId) {
            submitButton = document.querySelector(`#${config.modalId} .btn-primary`);
        }
        
        const originalText = submitButton ? submitButton.innerHTML : '';

        try {
            if (submitButton) {
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 上传中...';
                submitButton.disabled = true;
            }

            // 添加目标库参数
            formData.append('target_library', config.targetLibrary);

            const response = await fetch(config.apiEndpoint, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // 关闭模态框
                if (config.modalId) {
                    const modal = bootstrap.Modal.getInstance(document.getElementById(config.modalId));
                    if (modal) modal.hide();
                }

                // 重置表单
                form.reset();

                // 显示成功消息
                const successMessage = config.targetLibrary === 'reference' 
                    ? `配方添加成功！<br>配方ID: ${result.formula_id}<br>成分数: ${result.ingredients_count}<br>已添加到参考配方库`
                    : `上传成功！配方ID: ${result.formula_id}, 成分数: ${result.ingredients_count}`;
                
                AlertSystem.showAlert('success', successMessage);

                // 执行成功回调
                if (config.successCallback) {
                    config.successCallback(result);
                }
            } else {
                const errorMessage = '上传失败：' + (result.detail || result.message || '未知错误');
                AlertSystem.showAlert('danger', errorMessage);
                
                if (config.errorCallback) {
                    config.errorCallback(result);
                }
            }
        } catch (error) {
            console.error('上传错误:', error);
            const errorMessage = '上传失败：' + error.message;
            AlertSystem.showAlert('danger', errorMessage);
            
            if (config.errorCallback) {
                config.errorCallback(error);
            }
        } finally {
            if (submitButton) {
                submitButton.innerHTML = originalText;
                submitButton.disabled = false;
            }
        }
    }
}

// =============================================
// 8. 全局实例和工具函数
// =============================================

// 全局工具函数（保持向后兼容性）
window.showAlert = AlertSystem.showAlert;
window.FileNameUtils = FileNameUtils;
window.ProductTypeRecognizer = ProductTypeRecognizer;

// 全局错误处理：监听所有fetch请求的401错误
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    try {
        const response = await originalFetch(...args);
        
        // 检查是否是401未登录错误
        if (response.status === 401) {
            try {
                const errorData = await response.clone().json();
                if (errorData.detail && errorData.detail.includes('未登录')) {
                    // 显示提示并跳转到登录页面
                    GlobalNotificationSystem.showNotification('warning', '登录状态已过期，正在跳转到登录页面...', { duration: 2000 });
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 1000);
                    return response;
                }
            } catch (e) {
                // 如果解析错误信息失败，直接跳转
                console.warn('解析401错误信息失败，直接跳转到登录页面');
                window.location.href = '/';
            }
        }
        
        return response;
    } catch (error) {
        throw error;
    }
};

// 登出功能（通用）
window.logout = async function() {
    try {
        const response = await fetch('/api/v1/auth/logout', {
            method: 'POST'
        });

        const data = await response.json();
        if (data.success) {
            GlobalNotificationSystem.showNotification('success', '登出成功！正在跳转...', { duration: 1500 });
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('登出失败:', error);
        window.location.href = '/';
    }
};

// 修改密码功能
window.showChangePasswordModal = function() {
    const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
    modal.show();
};

window.submitChangePassword = async function() {
    const form = document.getElementById('changePasswordForm');
    const formData = new FormData(form);
    
    // 获取表单数据
    const currentPassword = formData.get('current_password');
    const newPassword = formData.get('new_password');
    const confirmPassword = formData.get('confirm_password');
    
    // 前端验证
    if (!currentPassword || !newPassword || !confirmPassword) {
        GlobalNotificationSystem.showNotification('warning', '请填写完整的密码信息');
        return;
    }
    
    if (newPassword !== confirmPassword) {
        GlobalNotificationSystem.showNotification('warning', '两次输入的新密码不一致');
        return;
    }
    
    if (newPassword.length < 4 || newPassword.length > 16) {
        GlobalNotificationSystem.showNotification('warning', '新密码长度必须在4-16位之间');
        return;
    }
    
    if (currentPassword === newPassword) {
        GlobalNotificationSystem.showNotification('warning', '新密码不能与当前密码相同');
        return;
    }
    
    // 显示加载状态
    const submitBtn = document.querySelector('#changePasswordModal .btn-primary');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>修改中...';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/api/v1/auth/change-password', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            GlobalNotificationSystem.showNotification('success', data.message || '密码修改成功！');
            
            // 关闭模态框
            const modal = bootstrap.Modal.getInstance(document.getElementById('changePasswordModal'));
            modal.hide();
            
            // 重置表单
            form.reset();
        } else {
            GlobalNotificationSystem.showNotification('danger', data.message || '密码修改失败');
        }
    } catch (error) {
        console.error('修改密码失败:', error);
        GlobalNotificationSystem.showNotification('danger', '密码修改失败，请稍后重试');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
};
