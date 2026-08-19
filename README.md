<div align="center">

# 化妆品配方表匹配系统

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![Version](https://img.shields.io/badge/version-v3.0.0-brightgreen.svg)
![Database](https://img.shields.io/badge/database-MySQL8-orange.svg)

**化妆品配方分析与匹配平台（双配方库版本）**

[项目简介](#-项目简介) •
[功能特性](#-功能特性) •
[快速开始](#-快速开始) •
[使用指南](#-使用指南) •
[API文档](#-api文档) •
[算法说明](#-算法说明) •
[项目结构](#-项目结构)

</div>

---

## 🚀 项目简介

化妆品配方表匹配系统是一个面向化妆品行业的智能配方分析与匹配平台。系统采用**双配方库架构**（参考配方库 + 待匹配配方库），支持 Excel 配方表自动解析、复配成分识别、基于**两段式相似度算法**的智能匹配、配方对比分析，并提供完整的用户认证、权限控制和系统配置能力。

系统由 FastAPI 提供后端 API 与页面渲染，Bootstrap 5 + 原生 JavaScript 提供前端交互，MySQL 8.0 存储数据，Scikit-learn 提供余弦相似度计算。

### 核心价值

- **智能匹配**：成分组成（加权 Jaccard）+ 成分比例（加权余弦）两段式相似度计算
- **双库架构**：参考配方库（被匹配）与待匹配配方库（用户上传）分离管理
- **复配识别**：支持 Excel 中同序号复配成分的自动分组与结构化处理
- **Excel 解析**：智能表头识别、合并单元格处理、批量导入（按文件夹结构自动归类）
- **权限体系**：管理员 / 普通用户角色，管理员可管理用户与系统配置
- **Web 界面**：配方库管理、上传匹配、对比分析、系统配置全功能页面

---

## ✨ 功能特性

### 📊 配方表解析（FormulaParser）

- 支持 `.xlsx` / `.xls` 格式，自动在 Excel 前 10 行中查找表头（关键词匹配 ≥3 个）
- 列名智能映射：序号、标准中文名称 / 中文名称、INCI 名称 / 英文名称、原料含量、成分含量、实际含量、使用目的、备注
- 合并单元格 NaN 自动向前填充，复配成分（含"复配、混合、复合、体系"等关键词）自动标记
- 解析后数据校验：缺名称、缺含量、含量超 100%、总含量偏离 100% 等告警与错误统计

### 🎯 智能匹配引擎（DualLibraryMatchingEngine）

- **两段式算法**：成分组成相似度（按分类加权 Jaccard）+ 成分比例相似度（并集加权余弦）
- **六大分类权重**：防腐剂、乳化剂、增稠剂、抗氧化剂、表面活性剂、其他（总和须为 1.0）
- **严格范围匹配**：仅匹配相同产品类型与客户的配方；常规模式匹配全库
- **复配整体处理**：复配成分按成分组合生成稳定标识参与匹配
- **匹配统计**：平均 / 最大 / 最小相似度、高 / 中 / 低相似度计数

### 🗄️ 双配方库管理

- **参考配方库**：批量导入、搜索、筛选、排序、卡片 / 表格双视图、添加、编辑、删除
- **待匹配配方库**：上传、列表、单个 / 批量删除，普通用户仅见自己的配方
- **批量导入**：选择文件夹后按 `主文件夹/客户/产品大类/产品小类/配方文件.xlsx` 自动归类
- **统计面板**：配方数、成分数、产品类型数、客户数、最后更新时间

### 🌐 Web 界面

- 登录 / 注册 / 修改密码 / 登出，401 自动跳转登录页
- 产品类型自动识别：先查映射表（精确 + 模糊），再按产品类型关键词匹配，可一键快速添加映射
- 客户输入自动补全（支持键盘上下键选择）
- 配方匹配结果展示、配方详情弹窗、**双配方对比分析**（共同成分 / 差异成分 / 分类统计 / 原料含量对比）
- 系统配置页：分类权重、匹配参数、产品类型、映射管理、用户管理、系统统计

---

## 🏗️ 系统架构

### 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.104.1 |
| Web 服务器 | Uvicorn | 0.24.0 |
| 数据库 | MySQL | 8.0+ |
| ORM | SQLAlchemy | 2.0.23 |
| 数据库驱动 | PyMySQL | 1.1.0 |
| 数据处理 | Pandas / NumPy | 2.1.3 / 1.24.3 |
| Excel 解析 | OpenPyXL | 3.1.2 |
| 科学计算 | Scikit-learn | 1.3.2 |
| 数据校验 | Pydantic | 2.5.0 |
| 模板引擎 | Jinja2 | 3.1.2 |
| 表单 / 文件 | python-multipart | 0.0.6 |
| 前端 | Bootstrap 5.1.3 + Font Awesome 6（CDN） | - |

### 模块架构

```
src/
├── backend/                    # 后端核心模块
│   ├── api/                    # API 路由
│   │   ├── auth.py             # 认证：登录 / 注册 / 登出 / 改密
│   │   ├── reference_library.py# 参考配方库管理
│   │   ├── matching.py         # 上传、匹配、对比分析
│   │   └── system_config.py    # 系统配置、产品类型、用户管理
│   ├── sql/                    # 数据库层
│   │   ├── mysql_config.py     # MySQL 连接与初始化
│   │   └── mysql_models.py     # ORM 模型、配置管理器、双库处理器
│   ├── app_factory.py          # 应用工厂（中间件 / 静态文件 / 路由注册）
│   ├── dependencies.py         # 依赖注入、数据库会话、匹配引擎单例
│   ├── pages.py                # 页面路由（登录 / 主页 / 管理页）
│   ├── formula_parser.py       # Excel 配方表解析器
│   └── dual_library_matching_engine.py  # 双配方库匹配引擎
└── frontend/                   # 前端资源
    ├── static/
    │   ├── css/                # components / login / upload-match 等样式
    │   └── js/                 # common.js 共享组件 + 各页面脚本
    └── templates/              # Jinja2 页面模板
```

### 数据库架构

系统启动时自动建表（`Base.metadata.create_all`），共 8 张表：

| 表名 | 说明 |
|------|------|
| `users` | 用户表（username / password / role / is_active 等） |
| `ingredient_catalog` | 化妆品原料目录 |
| `formulas` | 参考配方主表 |
| `formula_ingredients` | 参考配方成分表 |
| `formulas_to_be_matched` | 待匹配配方主表 |
| `formula_ingredients_to_be_matched` | 待匹配配方成分表 |
| `formula_match_records` | 匹配记录表（相似度、分类相似度、匹配详情 JSON） |
| `system_config` | 系统配置键值表（分类权重、匹配参数、产品类型、映射表） |

> 同一 `ingredient_id` 下有多条 `ingredient_sequence` 记录即视为复配成分；成分表以 `DECIMAL(12,8)` 高精度存储含量。

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone <仓库地址>
cd cosmetic-formula-table-matching-system
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置数据库（mysql_config.ini）

```ini
[database]
host = localhost
port = 3306
username = cosmetic_user
password = your_password
database = cosmetic_formula_db
charset = utf8mb4

[connection]
pool_size = 5
max_overflow = 10
pool_timeout = 30
pool_recycle = 3600
```

### 4. 配置系统（system_config.ini）

```ini
[admin]
username = admin
password = your_admin_password

[security]
session_timeout = 3600
password_min_length = 4
password_max_length = 16

[system]
debug = False
log_level = INFO
backup_enabled = True
```

### 5. 启动系统

```bash
python main.py
```

首次启动会自动完成：连接 MySQL、创建数据表、初始化默认系统配置、创建 / 同步管理员账号（取自 `system_config.ini` 的 `[admin]` 段）。

### 6. 访问系统

| 页面 | 地址 |
|------|------|
| 登录页 | http://127.0.0.1:8000 |
| 系统主页 | http://127.0.0.1:8000/dashboard |
| 配方表匹配 | http://127.0.0.1:8000/upload-match |
| 配方库管理 | http://127.0.0.1:8000/reference-library |
| 系统配置（仅管理员） | http://127.0.0.1:8000/system-config |
| API 文档（仅管理员导航可见） | http://127.0.0.1:8000/docs |

> 前端页面通过 CDN 加载 Bootstrap 与 Font Awesome，离线环境需自行将资源改为本地文件。

---

## 📋 使用指南

### 配方库管理（/reference-library）

1. **添加配方**：选择 Excel 文件，填写配方名称（默认取文件名）、产品大类 / 细分类型（支持自动识别与快速映射）、客户，上传至参考配方库。
2. **批量导入**：选择包含配方文件的文件夹，系统按 `主文件夹/客户/产品大类/产品小类/配方文件.xlsx` 的结构自动归类，先预览后导入。
3. **列表管理**：支持名称搜索、产品类型 / 客户筛选、更新时间 / 名称 / 成分数排序，卡片与表格双视图；管理员或上传者可编辑、删除配方。

### 配方表匹配（/upload-match）

1. **上传待匹配配方**：选择 Excel 文件，填写配方名称、产品类型、客户，上传至待匹配配方库（同名校验）。
2. **执行匹配**：可切换「严格范围匹配」（默认开启，仅匹配相同产品类型与客户）或全库匹配，点击匹配按钮后系统对配方库全量计算相似度并返回 Top 5 结果。
3. **结果分析**：查看每个结果的相似度得分、组成 / 比例相似度、分类相似度、共同成分；可进入配方详情或发起**双配方对比分析**（共同成分、差异成分、分类分组、原料实际含量对比；对比结果导出功能为占位，开发中）。

### 系统配置（/system-config，仅管理员）

1. **分类权重**：六大分类权重（总和必须为 1.0）。
2. **匹配算法参数**：组成相似度权重、比例相似度权重（和为 1.0）、复配匹配阈值、最小相似度阈值。
3. **产品类型**：管理产品大类与细分类型（默认含"驻留类 / 淋洗类 / 其他类"）。
4. **产品类型映射**：将不规则配方名称映射到标准产品类型，上传时优先使用映射表识别。
5. **用户管理**：添加 / 编辑 / 删除用户、修改角色、启停账户、重置密码（不可删除或停用自己、不可删除最后一个管理员）。

---

## 📚 API 文档

所有接口前缀 `/api/v1`，页面 API 以表单（Form）提交，配置类 API 以 JSON 提交。启动后可访问 http://127.0.0.1:8000/docs 查看交互式文档。

### 认证接口（auth.py）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/auth/login` | POST | 登录（Form：username, password） |
| `/api/v1/auth/register` | POST | 注册（Form：username, password） |
| `/api/v1/auth/logout` | POST | 登出 |
| `/api/v1/auth/user` | GET | 获取当前用户信息 |
| `/api/v1/auth/change-password` | POST | 修改密码（Form：current_password, new_password, confirm_password） |

### 参考配方库接口（reference_library.py）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/reference-library-stats` | GET | 配方库统计（总数 / 成分数 / 产品类型 / 客户 / 更新时间） |
| `/api/v1/reference-formulas` | GET | 配方列表（skip / limit / search / product_type，需登录） |
| `/api/v1/reference-formulas/{id}` | GET | 配方详情（含成分与结构） |
| `/api/v1/reference-formulas/{id}` | PUT | 编辑配方（管理员或上传者，可选重新上传文件） |
| `/api/v1/reference-formulas/{id}` | DELETE | 删除配方（管理员或上传者，级联删除成分与匹配记录） |

### 配方匹配接口（matching.py）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/to-match-formulas` | GET | 待匹配配方列表（管理员全量，普通用户仅自己的） |
| `/api/v1/to-match-formulas/{id}` | DELETE | 删除待匹配配方 |
| `/api/v1/to-match-formulas/batch` | DELETE | 批量删除（JSON：formula_ids） |
| `/api/v1/upload-formula` | POST | 统一上传（multipart：file, formula_name, product_type, customer, target_library=reference / to_match） |
| `/api/v1/match-formula/{id}` | POST | 执行匹配（query：strict_mode=true/false） |
| `/api/v1/formula-detail/{id}` | GET | 配方详情（query：formula_type=reference / to_be_matched） |
| `/api/v1/customers` | GET | 客户列表（合并两库去重排序） |
| `/api/v1/formula-comparison` | POST | 双配方对比分析（JSON：source_formula_id, target_formula_id） |

### 系统配置接口（system_config.py）

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/stats` | GET | 系统统计（原料目录 / 两库配方与成分 / 匹配记录 / 配置数） |
| `/api/v1/config/category-weights` | GET / PUT | 获取 / 更新分类权重（PUT 需 JSON 六类权重，总和为 1.0） |
| `/api/v1/config/matching-parameters` | GET / PUT | 获取 / 更新匹配参数（组成权重 + 比例权重 = 1.0） |
| `/api/v1/config/product-types` | GET / PUT | 获取 / 更新产品类型配置 |
| `/api/v1/config/initialize` | POST | 初始化默认系统配置 |
| `/api/v1/config/product-type-mappings` | GET / POST / DELETE / PUT | 映射表查询、添加（from_name, to_product_type）、删除、批量设置 |
| `/api/v1/users` | GET / POST | 用户列表 / 创建用户（仅管理员） |
| `/api/v1/users/{user_id}` | PUT / DELETE | 更新 / 删除用户（仅管理员） |
| `/api/v1/users/{user_id}/reset-password` | POST | 重置用户密码（仅管理员） |

### 页面路由（pages.py）

| 路径 | 说明 | 权限 |
|------|------|------|
| `/` | 登录页（已登录跳转 /dashboard） | 公开 |
| `/dashboard` | 系统主页 | 需登录 |
| `/reference-library` | 配方库管理 | 需登录 |
| `/upload-match` | 上传与匹配 | 需登录 |
| `/system-config` | 系统配置 | 仅管理员 |

---

## 🧮 算法说明

### 两段式相似度计算

总相似度 = `组成相似度权重 × 成分组成相似度 + 比例相似度权重 × 成分比例相似度`，默认权重为 **0.8 / 0.2**。

#### 1. 成分组成相似度（按分类加权 Jaccard）

- 将配方成分按"使用目的"关键词映射到六大标准分类（防腐剂 / 乳化剂 / 增稠剂 / 抗氧化剂 / 表面活性剂 / 其他）
- 对每个分类分别计算 `Jaccard = |交集| / |并集|`（单配成分以原料目录 ID 标识，复配以成分组合哈希标识）
- 只对实际存在成分的分类加权平均：`组成相似度 = Σ(分类权重 × 分类 Jaccard) / Σ(有效分类权重)`

#### 2. 成分比例相似度（并集加权余弦）

- 取两个配方所有成分的并集构建含量向量（复配作为整体参与）
- 计算余弦相似度：`比例相似度 = cos(源配方向量, 目标配方向量)`

#### 3. 复配成分处理

- Excel 中序号相同的多行视为一个复配整体；解析器同时按"复配 / 混合 / 复合 / 体系"等关键词标记
- 复配以排序后前 3 个成分名称的 MD5 哈希作为稳定标识，保证同一复配在不同配方中标识一致
- `复配匹配阈值`（默认 0.6）用于判断复配是否匹配成功


### 默认参数

| 参数 | 默认值 | 说明 |
|------|------|------|
| 组成 / 比例权重 | 0.8 / 0.2 | 两段相似度加权 |
| 分类权重 | 防腐剂 0.35，乳化剂 0.15，增稠剂 0.15，抗氧化剂 0.10，表面活性剂 0.10，其他 0.15 | 分类加权 Jaccard |
| 复配匹配阈值 | 0.6 | 复配匹配成功判定 |
| 最小相似度阈值 | 0.0 | 结果过滤 |
| 最大结果数 | 5 | 每个配方返回 Top 5（当前写死） |

### 匹配范围

- **常规模式**：对待匹配配方与参考配方库全量匹配
- **严格模式**：按产品类型（支持"大类-小类"新格式与仅大类的旧格式兼容匹配）与客户过滤候选配方

---

## ⚙️ 配置说明

### 数据库配置（mysql_config.ini）

`[database]`：host / port / username / password / database / charset

`[connection]`：连接池参数（pool_size=5, max_overflow=10, pool_timeout=30, pool_recycle=3600）

`[logging]`：log_level / enable_sql_echo

### 系统配置（system_config.ini）

`[admin]`：管理员用户名与密码（启动时用于初始化 / 同步管理员账户）

`[security]`：session_timeout（会话超时，秒）、password_min_length、password_max_length

`[system]`：debug / log_level / backup_enabled

> `.env.mysql` 是环境变量格式的示例文件，当前代码实际读取 `mysql_config.ini`，未使用 `.env` 文件；两者均已被 `.gitignore` 忽略。

---

## 🗂️ 项目结构

```
├── main.py                     # 应用入口，uvicorn 启动（127.0.0.1:8000）
├── requirements.txt            # 依赖清单
├── mysql_config.ini            # 数据库配置
├── system_config.ini           # 系统 / 管理员 / 安全配置
├── .env.mysql                  # 环境变量示例（当前代码未读取）
├── auto_restart_services.sh    # Linux 服务自动重启脚本（systemd）
├── quick_restart.sh            # Linux 快速重启脚本
├── docs/
│   └── 化妆品原料目录.xlsx       # 原料目录示例数据
└── src/
    ├── backend/
    │   ├── app_factory.py
    │   ├── dependencies.py
    │   ├── pages.py
    │   ├── formula_parser.py
    │   ├── dual_library_matching_engine.py
    │   ├── api/
    │   │   ├── auth.py
    │   │   ├── reference_library.py
    │   │   ├── matching.py
    │   │   └── system_config.py
    │   └── sql/
    │       ├── mysql_config.py
    │       └── mysql_models.py
    └── frontend/
        ├── templates/          # login / dashboard / reference-library / upload-match / system-config
        └── static/
            ├── css/            # 页面样式
            └── js/             # common.js + 各页面脚本
```

---

## 🔧 开发指南

### 环境搭建

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python main.py                # 开发调试
```

### 如何添加功能

1. 在 `src/backend/api/` 添加 API 路由模块，并在 `app_factory.py` 的 `register_routes()` 中注册
2. 新增数据模型时在 `src/backend/sql/mysql_models.py` 中定义，启动时自动建表
3. 页面模板放 `src/frontend/templates/`，脚本与样式放 `src/frontend/static/`
4. 页面路由在 `src/backend/pages.py` 中注册

### 代码约定

- API 统一前缀 `/api/v1`，页面 API 使用 Form 提交，配置 API 使用 JSON
- 权限控制通过 `dependencies.py` 中的 `require_login` / `require_admin` 依赖实现
- 匹配引擎为单例（`get_matching_engine`），每次匹配前从数据库重新加载最新参数

---

## ⚠️ 已知说明与注意事项

- **对比导出**：前端"导出对比"按钮为占位实现，提示"开发中"
- **测试**：当前仓库无 `tests/` 目录，尚未提供自动化测试
- **样式**：`src/frontend/static/css/global.css` 为空文件；`dashboard.css` 内容较少
- **安全**：会话密钥为硬编码字符串，密码使用 SHA-256 哈希（未加盐）存储，CORS 允许所有来源；生产环境请修改 `app_factory.py` 中的 `secret_key`、配置文件中的管理员密码，并按需收紧 CORS
- **监听地址**：`main.py` 默认仅监听 `127.0.0.1:8000`；如需对外提供服务，可配合 Nginx 反向代理（部署脚本默认约定 Nginx 端口 8010）
- **许可证**：仓库当前未附带 LICENSE 文件

---

## 🚢 Linux 部署脚本

仓库提供两个基于 systemd 的运维脚本（目标路径约定 `/opt/cosmetic_formula_system`，服务单元 `mysql`、`cosmetic-formula`、`nginx`）：

### auto_restart_services.sh（完整版）

```bash
sudo ./auto_restart_services.sh              # 完全重启（MySQL + 应用 + Nginx）
sudo ./auto_restart_services.sh app          # 只重启应用
sudo ./auto_restart_services.sh graceful     # 优雅重启（等待现有连接结束）
sudo ./auto_restart_services.sh --check      # 仅检查服务状态
sudo ./auto_restart_services.sh -b -f        # 备份配置并强制重启
```

支持模式：`full` / `app` / `web` / `db` / `graceful`；支持选项 `-h`（帮助）、`-v`（详细）、`-f`（强制）、`-b`（备份）、`-c`（检查）、`-t`（测试模式）。包含健康检查、端口检测、等待启动、配置备份与日志记录（`/var/log/cosmetic_formula_restart.log`）。

### quick_restart.sh（简化版）

```bash
sudo ./quick_restart.sh
```

停止并重启应用与 Nginx（MySQL 未运行时自动启动），随后检查服务状态、端口监听与 HTTP 连通性。

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 打开 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 添加适当的注释和文档
- 新增功能后更新本文档

---

<div align="center">

**[⬆ 回到顶部](#化妆品配方表匹配系统)**

</div>
