<div align="center">

# 化妆品配方表匹配系统

</div>

<div align="center">

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-v3.0.0-brightgreen.svg)

**化妆品配方分析与匹配平台**

[功能特性](#功能特性) •
[快速开始](#快速开始) •
[API文档](#api文档) •
[系统架构](#系统架构) •
[使用指南](#使用指南)

</div>

---

## 🚀 项目简介

化妆品配方表匹配系统是一个专为化妆品行业设计的智能配方分析与匹配平台。系统采用双配方库架构，支持Excel配方表解析，提供基于机器学习的智能匹配算法，帮助用户快速找到相似配方并进行配方分析。

### 🎯 核心价值

- **智能匹配**: 基于成分组成和比例的两段式相似度计算算法
- **双库架构**: 配方库(参考数据) + 待匹配配方库(用户数据)分离管理
- **Excel支持**: 自动解析Excel配方表，支持复配成分识别
- **Web界面**: 直观的Web界面，支持配方管理、匹配分析、系统配置
- **权限管理**: 完整的用户认证和权限控制系统

---

## ✨ 功能特性

### 📊 配方表解析
- 🔍 **智能表头识别**: 自动识别Excel配方表的表头结构
- 📝 **成分提取**: 准确提取中文名称、INCI名称、含量等信息
- 🔗 **复配识别**: 支持复配成分的自动识别和结构化处理
- ✅ **数据验证**: 完整的配方数据验证和错误检测

### 🎯 智能匹配引擎
- 🧮 **两段式算法**: 成分组成相似度 + 成分比例相似度
- 🏷️ **分类权重**: 支持防腐剂、乳化剂、增稠剂等6大分类权重配置
- 🔄 **算法参数**: 可配置的匹配算法参数和阈值
- 📈 **匹配结果**: 详细的相似度分析和匹配统计信息

### 🗄️ 双配方库管理
- 📚 **配方库**: 参考配方数据管理，支持批量导入
- 📋 **待匹配库**: 用户上传配方管理，支持匹配操作
- 🔄 **数据同步**: 配方数据的增删改查操作
- 📊 **统计分析**: 配方库使用统计和分析报告

### 🌐 Web界面
- 🎨 **现代UI**: 基于Bootstrap的响应式Web界面
- 👤 **用户管理**: 完整的用户注册、登录、权限管理
- ⚙️ **系统配置**: 可视化的系统参数配置界面
- 📱 **移动支持**: 支持移动设备访问

---

## 🏗️ 系统架构

### 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| **后端框架** | FastAPI | 0.104.1 |
| **Web服务器** | Uvicorn | 0.24.0 |
| **数据库** | MySQL | 8.0+ |
| **ORM** | SQLAlchemy | 2.0.23 |
| **数据处理** | Pandas | 2.1.3 |
| **机器学习** | Scikit-learn | 1.3.2 |
| **前端** | Bootstrap 5 + jQuery | - |

### 模块架构

```
src/
├── backend/              # 后端核心模块
│   ├── api/             # API路由
│   │   ├── auth.py          # 用户认证
│   │   ├── matching.py      # 配方匹配
│   │   ├── reference_library.py  # 配方库管理
│   │   └── system_config.py # 系统配置
│   ├── sql/             # 数据库层
│   │   ├── mysql_config.py  # 数据库配置
│   │   └── mysql_models.py  # 数据模型
│   ├── app_factory.py   # 应用工厂
│   ├── dependencies.py  # 依赖注入
│   ├── formula_parser.py # 配方解析器
│   ├── dual_library_matching_engine.py # 匹配引擎
│   └── pages.py         # 页面路由
└── frontend/            # 前端资源
    ├── static/          # 静态文件
    │   ├── css/         # 样式文件
    │   └── js/          # JavaScript
    └── templates/       # HTML模板
```

### 数据库架构

```sql
-- 配方库表组 (参考配方)
├── formulas                    # 配方主表
├── formula_ingredients         # 配方成分表

-- 待匹配配方表组 (用户配方)
├── formulas_to_be_matched     # 待匹配配方主表  
├── formula_ingredients_to_be_matched # 待匹配配方成分表

-- 支持表组
├── ingredient_catalog          # 原料目录
├── formula_match_records      # 匹配记录
├── system_config              # 系统配置
└── users                      # 用户表
```

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone https://github.com/yanglinbin/cosmetic-formula-matching-system.git
cd cosmetic-formula-matching-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 数据库配置

复制并编辑数据库配置文件：

```bash
# 编辑 mysql_config.ini
[database]
host = localhost
port = 3306
username = your_username
password = your_password
database = cosmetic_formula_db
charset = utf8mb4
```

### 4. 系统配置

编辑 `system_config.ini` 文件：

```ini
[admin]
username = admin
password = your_admin_password

[security]
session_timeout = 3600
password_min_length = 4

[system]
debug = False
log_level = INFO
```

### 5. 启动系统

```bash
python main.py
```

系统将在 `http://localhost:8000` 启动。

### 6. 访问系统

- **主页**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **配方库管理**: http://localhost:8000/reference-library
- **配方匹配**: http://localhost:8000/upload-match
- **系统配置**: http://localhost:8000/system-config

---

## 📋 使用指南

### 配方库管理

1. **上传配方表**
   - 支持 `.xlsx` 和 `.xls` 格式
   - 自动识别表头结构
   - 批量导入多个配方

2. **配方数据管理**
   - 查看配方详情
   - 编辑配方信息
   - 删除配方数据

### 配方匹配

1. **上传待匹配配方**
   - 上传Excel配方表
   - 设置产品类型和客户信息
   - 选择匹配模式

2. **执行匹配**
   - 选择匹配范围 (全库/限定范围)
   - 设置相似度阈值
   - 查看匹配结果

3. **结果分析**
   - 相似度详细分析
   - 共同成分对比
   - 匹配统计报告

### 系统配置

1. **分类权重配置**
   ```json
   {
     "防腐剂": 0.35,
     "乳化剂": 0.15,
     "增稠剂": 0.15,
     "抗氧化剂": 0.10,
     "表面活性剂": 0.10,
     "其他": 0.15
   }
   ```

2. **匹配算法参数**
   - 成分组成权重: 0.8
   - 成分比例权重: 0.2
   - 复配匹配阈值: 0.6
   - 最小相似度阈值: 0.0

---

## 📚 API文档

### 认证接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 用户登录 |
| `/api/v1/auth/register` | POST | 用户注册 |
| `/api/v1/auth/logout` | POST | 用户登出 |
| `/api/v1/auth/user` | GET | 获取用户信息 |

### 配方库接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/reference/upload` | POST | 上传配方表 |
| `/api/v1/reference/formulas` | GET | 获取配方列表 |
| `/api/v1/reference/formula/{id}` | GET | 获取配方详情 |
| `/api/v1/reference/formula/{id}` | DELETE | 删除配方 |

### 匹配接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/matching/upload` | POST | 上传待匹配配方 |
| `/api/v1/matching/execute` | POST | 执行配方匹配 |
| `/api/v1/matching/results/{id}` | GET | 获取匹配结果 |

### 配置接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/config/category-weights` | GET/POST | 分类权重配置 |
| `/api/v1/config/matching-params` | GET/POST | 匹配参数配置 |
| `/api/v1/config/product-types` | GET/POST | 产品类型配置 |

---

## ⚙️ 配置说明

### 数据库配置 (mysql_config.ini)

```ini
[database]
host = localhost          # 数据库主机
port = 3306              # 数据库端口
username = root          # 数据库用户名
password = your_password # 数据库密码
database = cosmetic_formula_db # 数据库名
charset = utf8mb4        # 字符集

[connection]
pool_size = 5           # 连接池大小
max_overflow = 10       # 最大溢出连接数
pool_timeout = 30       # 连接超时时间
pool_recycle = 3600     # 连接回收时间
```

### 系统配置 (system_config.ini)

```ini
[admin]
username = admin        # 管理员用户名
password = your_password # 管理员密码

[security]
session_timeout = 3600  # 会话超时时间(秒)
password_min_length = 4 # 密码最小长度
password_max_length = 16 # 密码最大长度

[system]
debug = False          # 调试模式
log_level = INFO       # 日志级别
backup_enabled = True  # 备份功能
```

---

## 🧮 算法说明

### 两段式相似度计算

系统采用创新的两段式相似度计算算法：

1. **成分组成相似度** (权重: 0.8)
   - 基于加权Jaccard系数
   - 按分类计算相似度
   - 支持复配成分匹配

2. **成分比例相似度** (权重: 0.2)
   - 基于余弦相似度
   - 考虑成分含量差异
   - 向量化比例计算

### 分类权重系统

支持6大成分分类的权重配置：

- **防腐剂**: 35% (最关键)
- **乳化剂**: 15%
- **增稠剂**: 15%
- **抗氧化剂**: 10%
- **表面活性剂**: 10%
- **其他**: 15%

---

## 🔧 开发指南

### 开发环境搭建

1. **虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **安装开发依赖**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio  # 测试工具
   ```

3. **代码风格**
   ```bash
   pip install black flake8  # 代码格式化
   black src/
   flake8 src/
   ```

### 项目结构说明

- `main.py`: 应用入口文件
- `src/backend/`: 后端核心代码
- `src/frontend/`: 前端静态资源
- `docs/`: 项目文档和示例数据
- `tests/`: 测试代码 (待完善)

### 添加新功能

1. 在 `src/backend/api/` 添加新的API路由
2. 在 `src/backend/sql/mysql_models.py` 添加数据模型
3. 在 `src/frontend/templates/` 添加页面模板
4. 在 `src/frontend/static/` 添加静态资源

---

### 日志查看

系统日志包含详细的运行信息：

```bash
# 查看应用日志
tail -f app.log

# 查看错误日志  
grep "ERROR" app.log
```

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加适当的注释和文档
- 编写测试用例
- 更新相关文档

---

<div align="center">

**[⬆ 回到顶部](#化妆品配方表匹配系统)**

---

Made with ❤️ by [yilabao](https://github.com/yanglinbin)

</div>
