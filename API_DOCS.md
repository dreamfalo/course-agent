# 智能课程助手 Agent - REST API 文档

> 基于 Django 4.2 + DRF + LangChain DeepSeek Agent 内核

## 基础信息

- Base URL: `http://localhost:8000/api`
- 鉴权方式: Bearer Token (JWT)
- 数据格式: JSON
- 字符编码: UTF-8

## 通用响应格式

```json
{
  "code": 0,
  "msg": "success",
  "data": { ... }
}
```

分页列表响应:
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5,
    "results": [ ... ]
  }
}
```

> 所有列表接口支持 `?page=1&page_size=20` 分页参数，`page_size` 最大 100。

---

## 1. 鉴权

### POST /api/auth/login/
登录获取 JWT Token

**Body:**
```json
{"username": "student01", "password": "pass1234"}
```

**Response:**
```json
{"refresh": "...", "access": "..."}
```

### POST /api/auth/refresh/
刷新 Token

### POST /api/config/user/register/
用户注册（无需鉴权）
```json
{"username": "newuser", "password": "pass1234", "email": "a@b.com", "role": "student"}
```

### GET /api/config/user/me/
获取当前用户信息

---

## 2. 课表管理 - /api/schedule/

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/schedule/ | 查询课表（支持 ?semester=&weekday= 筛选） |
| POST | /api/schedule/ | 添加课程（自动冲突校验） |
| PUT | /api/schedule/{id}/ | 更新课程 |
| PATCH | /api/schedule/{id}/ | 部分更新 |
| DELETE | /api/schedule/{id}/ | 删除课程 |
| POST | /api/schedule/batch_import/ | 批量导入课表 |
| GET | /api/schedule/export/ | 导出课表 CSV（?format=csv） |

**添加课程 Body:**
```json
{
  "course_name": "高等数学",
  "teacher": "张教授",
  "weekday": 0,
  "start_time": "08:00",
  "end_time": "09:30",
  "location": "教学楼A101",
  "week_range": "1-16",
  "semester": "2025-2026-2"
}
```

**批量导入 Body:**
```json
{
  "courses": [
    {"course_name":"数学","weekday":0,"start_time":"08:00","end_time":"09:30"}
  ],
  "semester": "2025-2026-2"
}
```

---

## 3. 知识库 - /api/knowledge/

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/knowledge/ | 列出文档（?course_id= 筛选） |
| POST | /api/knowledge/ | 上传文件（multipart: file + course_id + course_name） |
| POST | /api/knowledge/search/ | 知识库语义检索 |
| GET | /api/knowledge/{id}/preview/ | 获取文档下载预览链接 |
| DELETE | /api/knowledge/{id}/ | 删除文档 |

**检索 Body:**
```json
{"query": "微积分基本概念", "course_id": "COURSE_MATH", "top_k": 5}
```

---

## 4. 学习任务 - /api/task/

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/task/ | 查询任务（?plan_id=&start_date=&end_date=） |
| POST | /api/task/ | 手动创建任务 |
| PUT/PATCH | /api/task/{id}/ | 更新任务进度 |
| DELETE | /api/task/{id}/ | 删除任务 |
| POST | /api/task/ai_generate/ | AI 一键生成学习计划 |
| GET | /api/task/gantt/ | 获取甘特图数据 |

**AI 生成 Body:**
```json
{
  "daily_study_hours": 3,
  "subjects": ["数学", "英语", "专业课"],
  "start_date": "2026-06-20",
  "days": 30
}
```

---

## 5. Agent 对话 - /api/agent/

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/agent/chat/ | Agent 对话入口（核心） |
| GET | /api/agent/history/ | 获取对话历史（?session_id=） |
| GET | /api/agent/sessions/ | 获取用户所有会话列表 |

**对话 Body:**
```json
{
  "message": "帮我查一下周三有什么课",
  "session_id": "",
  "role": "student"
}
```

**对话 Response:**
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "response": "您周三的课表如下：1. 计算机基础 08:00-09:30...",
    "session_id": "a1b2c3d4",
    "tool_calls": [
      {"tool": "schedule_tool", "input": {"action": "query"}, "output": "..."}
    ]
  }
}
```

---

## 6. 系统配置 - /api/config/

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/config/system/ | 列出配置（管理员） |
| PUT | /api/config/system/{id}/ | 修改配置 |
| GET | /api/config/system/public/ | 公开配置（无需鉴权） |

---

## 7. SWAGGER 文档

启动服务后访问: http://localhost:8000/api/docs/

## 8. 启动方式

```bash
# 1. 设置环境变量
$env:DJANGO_DEBUG = "True"
$env:MYSQL_DATABASE = "course_agent_db"
$env:MYSQL_PASSWORD = "your_password"

# 2. 建表（二选一）
mysql -u root -p < sql/init_tables.sql         # Navicat 直接执行
python manage.py migrate                        # Django 迁移

# 3. 种子数据
python seed_data.py

# 4. 启动服务
python manage.py runserver 0.0.0.0:8000

# 5. 测试
curl -X POST http://localhost:8000/api/agent/chat/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"帮我查一下课表"}'
```
