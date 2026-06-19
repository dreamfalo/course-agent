# 🤖 智能课程助手 Agent

> 基于 **LangChain + DeepSeek + Django + Vue3** 的智能课程管理平台  
> AI 驱动的课表管理、RAG 知识库检索、学习任务规划、多轮对话交互

## 📋 项目概述

智能课程助手 Agent 是一个面向高校学生的 **AI 课程管理平台**。以 DeepSeek 大模型为底层引擎，基于 LangChain 框架构建 Agent 智能调度核心，实现课表解析导入、知识库 RAG 检索、学习任务自动规划、自然语言对话交互等功能。

### 核心能力

- 🗓️ **课表管理** — 上传教务系统 PDF/CSV/Word 课表，自动解析课程信息
- 💬 **AI 对话** — 多轮对话交互，LangChain Agent 自主调用工具完成任务
- 📚 **RAG 知识库** — 课件上传、向量化入库、语义检索匹配
- 📊 **学习任务** — 读取课表自动生成预习/复习/刷题任务，甘特图展示
- 📝 **学习笔记** — 课程笔记增删改查，学习动态折线图
- ⚙️ **系统配置** — DeepSeek 模型参数调节、账户管理、角色权限

---

## 🧰 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **LLM** | DeepSeek Chat/Code API | 统一封装客户端，支持 temperature / top_p / 上下文长度 |
| **Agent 框架** | LangChain 1.x | Core Agent + Tool + AgentExecutor 自主调度 |
| **向量库** | Chroma + OpenAI Embeddings | 文档向量化存储，语义检索 |
| **后端** | Django 4.2 + DRF | RESTful API，JWT 鉴权，全局异常处理 |
| **数据库** | MySQL 8.0 (mysqlclient) | 5 张核心表，ORM + Navicat SQL |
| **文件存储** | MinIO | 课件、导出文件存储下载 |
| **前端** | Vue 3 + Vite + Element Plus + TypeScript | 三栏布局，品牌蓝配色 |
| **状态管理** | Pinia | 全局用户/模型参数/课程状态 |
| **部署** | Docker Compose | 一键启动全部服务 |

## 🤖 Agent 工具清单 (7 个 LangChain BaseTool)

LangChain Agent 自动注册 8 个标准工具，接收自然语言后自主决策调用：

### 1. ScheduleTool — 课表工具
查询课表 | 新增/编辑/删除课程 | 时间冲突校验 | 文件导出 (CSV/Excel/ICS) | 课程统计

### 2. RAGRetrieveTool — 知识库检索
PDF/Word/TXT 解析 | 文本分块 | Chroma 向量入库 | 语义检索 | 文档管理/删除

### 3. TaskPlanTool — 任务规划
读取课表自动生成学习任务 | 避让上课时段 | 甘特图结构化数据 | 任务增删改/优先级

### 4. FileManageTool — 文件管理
课件上传 | 临时文件清理 | 过期文件自动删除 | 导出文件下载

### 5. NoteTool — 笔记工具 (首页配套)
新建/修改/删除笔记 | 按课程/关键词检索 | 笔记导出文本文件

### 6. StatTool — 数据统计
每日学习时长统计 (近7天) | 折线图数据 | 本周课程/任务汇总

### 7. ConfigTool — 系统配置
DeepSeek API 密钥读写 | 模型参数 (temperature/上下文) | 用户信息修改 | 向量库配置

### 8. MemoryTool — 对话记忆
多轮对话上下文存取 | 对话历史 MySQL 持久化 | 按会话分组历史记录

---

## 📁 项目结构

`
智能课程助手agent/
├── agent_core/                    # LangChain Agent 内核
│   ├── llm/
│   │   └── deepseek_client.py     # DeepSeek LLM 客户端 (BaseChatModel)
│   ├── agent/
│   │   └── memory_manager.py      # ConversationBufferMemory + MySQL 持久化
│   ├── tools/
│   │   ├── schedule_tool.py       # 课表 CRUD 工具
│   │   ├── rag_retrieve_tool.py   # RAG 检索增强工具
│   │   ├── note_tool.py           # 笔记工具
│   │   ├── stat_tool.py           # 数据统计工具
│   │   └── config_tool.py         # 系统配置工具
│   ├── auth/
│   │   └── access_control.py      # 角色权限控制 (学生/管理员)
│   ├── config.py                  # Agent 全局配置
│   └── tests/                     # 单元测试
│
├── course_agent_backend/          # Django 后端
│   ├── settings.py                # 项目配置 (数据库/JWT/MinIO/CORS)
│   ├── urls.py                    # 路由聚合
│   ├── exceptions.py              # 全局异常捕获
│   └── minio_utils.py             # MinIO 工具类封装
│
├── schedule/                      # 课表模块
│   ├── models.py                  # UserSchedule ORM
│   ├── views.py                   # CRUD + PDF解析 + 文件导出
│   └── urls.py                    # /api/schedule/
│
├── knowledge/                     # 知识库模块
│   ├── models.py                  # UserKnowledgeFile ORM
│   └── views.py                   # 上传/向量化/检索
│
├── task/                          # 学习任务模块
│   ├── models.py                  # UserTask ORM
│   └── views.py                   # 任务CRUD + AI生成
│
├── agent_chat/                    # AI 对话模块
│   ├── models.py                  # AgentChatHistory ORM
│   └── views.py                   # /api/agent/chat
│
├── config/                        # 系统配置模块
│   ├── models.py                  # SystemConfig + SystemUser
│   └── views.py                   # 配置管理
│
├── frontend/                      # Vue3 前端
│   ├── src/views/
│   │   ├── HomeView.vue           # 首页 (笔记+学习动态)
│   │   ├── ScheduleView.vue       # 课表管理 (周/月视图)
│   │   ├── ChatView.vue           # AI 对话聊天
│   │   ├── KnowledgeView.vue      # 知识库管理
│   │   ├── TasksView.vue          # 学习任务甘特图
│   │   ├── SettingsView.vue       # 系统配置
│   │   └── LoginView.vue          # 登录页
│   ├── components/                # 公共组件 (10+个)
│   ├── layouts/Layout.vue         # 三栏布局 + 渐变导航
│   ├── router/index.ts            # Vue Router
│   ├── stores/                    # Pinia 状态管理
│   └── styles/global.css          # 全局样式 (#2981fd)
│
├── sql/init_tables.sql            # MySQL 建表 SQL
├── docker-compose.yml             # Docker 一键启动
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
├── seed_data.py                   # 测试数据脚本
└── API_DOCS.md                    # 接口文档
`


---

## 🚀 启动方法

### 前置要求

- Python 3.10+ / uv 包管理器
- Node.js 20+ / npm
- MySQL 8.0 (本地或 Docker)
- Docker Desktop (可选，用于一键部署)

### 方式一：Docker 一键启动（推荐）

```bash
# 1. 复制环境配置
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY 等

# 2. 启动全部服务 (MySQL + Chroma + MinIO + Django + Vue)
docker-compose up -d

# 3. 初始化数据库
docker exec course_backend python manage.py migrate
docker exec course_backend python seed_data.py

# 4. 访问
# 前端: http://localhost
# 后端 API: http://localhost:8000/api/
# MinIO 控制台: http://localhost:9001
```

### 方式二：本地开发启动

#### 1. 启动 MySQL

```bash
# Docker 方式
docker run -d --name course_mysql \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=course_agent_db \
  -p 3306:3306 mysql:8.0

# 或使用本地 MySQL + Navicat 执行 sql/init_tables.sql
```

#### 2. 后端启动

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境配置
cp .env.example .env
# 编辑 .env 填写 DEEPSEEK_API_KEY、数据库密码等

# 数据库迁移
python manage.py migrate

# 灌测试数据
python seed_data.py

# 启动开发服务器 (端口 8000)
python manage.py runserver 0.0.0.0:8000
```

#### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
# 开发服务器: http://localhost:5173
```

#### 4. 测试账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 学生 | student01 | pass1234 |
| 管理员 | admin | admin123 |

---

## 📱 界面介绍

### 🏠 首页 (Home)
- 左侧：**学习笔记** — 浅蓝背景卡片，支持笔记添加/修改/删除，按课程绑定
- 右侧：**学习动态** — 折线图展示一周每天学习时长，本周课程/任务统计

### 📅 课表管理 (Schedule)
- 左侧筛选：学期下拉 / 周次快捷键 (1-20周) / 设置当前周
- 顶部 Tab：「周视图」|「月视图」切换
- **上传课表**：支持教务系统 PDF (自动解析)、CSV (逗号分隔)、Word 文档
- 课程卡片：显示课程名、时间、地点、教师，点击查看详情
- 每次上传覆盖旧课表，导入后即时显示
- 底部「导出课表」— 下载 CSV 文件

### 💬 AI 对话 (Chat)
- 左侧：历史对话列表，支持新建/切换/删除对话
- 中间：对话气泡交互 (AI 白色气泡 / 用户蓝色气泡)，自带时间戳
- 底部输入框：文本输入 + 发送按钮
- 调用 /api/agent/chat，LangChain Agent 自主调用工具

### 📚 知识库 (Knowledge)
- 左侧筛选：学期 / 课程分类 / 文件类型
- 右侧：文件网格卡片展示
- 操作：批量上传 / 重新向量化 / 删除
- 支持 PDF、Word、TXT、Markdown 文件格式

### 📊 学习任务 (Tasks)
- 左侧筛选：任务状态 / 优先级复选框
- 右侧：**甘特图** 可视化展示任务时间线
- 「AI 生成学习任务」按钮触发 Agent 规划工具

### ⚙️ 系统配置 (Settings)
- 左侧菜单：DeepSeek 模型配置 / 向量库配置 / 课表导出 / 消息提醒 / 账号管理
- 右侧：表单卡片，底部保存按钮
- 模型参数：temperature / 上下文长度 / top_p / 最大输出 token

### 👤 登录页 (Login)
- 品牌蓝渐变背景，居中登录卡片
- 用户名 + 密码表单，JWT Token 鉴权

---

## 🔌 API 接口概览

| 模块 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 认证 | POST | /api/auth/login/ | JWT 登录获取 Token |
| 认证 | POST | /api/auth/refresh/ | Token 刷新 |
| 课表 | GET/POST | /api/schedule/ | 课表列表 / 新增 |
| 课表 | PUT/DELETE | /api/schedule/{id}/ | 课表修改 / 删除 |
| 课表 | POST | /api/schedule/upload_file/ | 上传课表文件解析导入 |
| 课表 | POST | /api/schedule/batch_import/ | JSON 批量导入 |
| 课表 | POST | /api/schedule/auto_import/ | 从教务系统自动抓取 |
| 课表 | GET | /api/schedule/export/ | 导出 CSV |
| 知识库 | POST | /api/knowledge/upload/ | 文件上传 |
| 知识库 | POST | /api/knowledge/vectorize/ | 文档向量化 |
| 知识库 | GET | /api/knowledge/search/ | 知识库检索 |
| 任务 | POST | /api/task/generate/ | AI 一键生成任务 |
| 任务 | GET | /api/task/gantt/ | 甘特图数据 |
| 对话 | POST | /api/agent/chat/ | AI 对话入口 |
| 配置 | GET/PUT | /api/config/ | 系统配置读写 |

详细接口文档见 ▶ [API_DOCS.md](./API_DOCS.md)

---

## 🎨 UI 设计规范

| 用途 | 色值 |
|------|------|
| 主品牌蓝 | #2981fd |
| 导航栏渐变 | #2b82fe |
| 按钮 Hover | #1a6fd6 |
| 选中浅蓝背景 | #e8f1fe |
| 卡片 Hover | #f0f7ff |
| 主标题文字 | #1f2937 |
| 正文文字 | #4b5563 |
| 辅助文字 | #9ca3af |

- 圆角 8px | 白底浅灰分割线 | 无多余阴影 | 16:9 宽屏
- 三栏布局 (左侧栏 + 中间主内容 + 右侧面板)

---

## 🔧 环境变量 (.env)

```env
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=course_agent_db
MYSQL_USER=root
MYSQL_PASSWORD=root

# Chroma
CHROMA_PERSIST_DIR=./chroma_db

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# OpenAI Embedding
OPENAI_API_KEY=sk-your-key-here

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=80
```

---

## 🧪 测试

```bash
# Agent 内核单元测试
python -m pytest agent_core/tests/ -v

# 全链路集成测试
python tests/full_chain_test.py
```

---

## 🐛 常见问题

**Q: MySQL 连接报 Access denied**
> 检查 .env 中 MYSQL_PASSWORD 是否正确

**Q: npm install 报 EPERM 权限错误**
> 以管理员身份运行终端，或清除缓存: npm cache clean --force

**Q: 上传课表返回「未识别到有效课程数据」**
> 确认文件为教务系统导出的标准 PDF，或 CSV 格式: 课程,教师,星期,开始时间,结束时间,地点,周次

**Q: AI 对话报错「DeepSeek client not initialized」**
> 确保 .env 中 DEEPSEEK_API_KEY 已正确填写，并重启后端

**Q: Chroma 向量检索无结果**
> 确保 OpenAI API Key 已配置 (Embeddings)，且文档已执行向量化

---

## 📄 License

MIT License — 仅供学习交流使用
