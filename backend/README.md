# Backend C - 视频处理 App 后端服务

FastAPI 后端，提供用户系统、视频上传、任务队列调度、AI 处理回调等完整功能。

## 技术栈

- **Framework**: FastAPI + Uvicorn
- **Database**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.x
- **Queue**: Redis List (RPUSH/BLPOP)
- **Auth**: JWT (python-jose) + bcrypt
- **Storage**: 本地文件系统 (可扩展为 OSS/S3)

## 快速启动

### 方式一：本地开发 (SQLite, 无需 Redis)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# 复制并编辑环境变量
cp .env.example .env

# 启动服务 (默认 SQLite，同步处理任务)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问:
- API 测试: http://localhost:8000/api/test
- Swagger 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

### 方式二：Docker Compose (推荐生产环境)

```bash
cd backend

# 编辑 .env 设置密钥
cp .env.example .env

# 启动全部服务 (PostgreSQL + Redis + Backend + Worker)
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
docker-compose logs -f worker
```

## API 接口文档

### 认证方式

所有需要登录的接口使用 `Authorization: Bearer <token>` 请求头。

### 接口列表

#### 用户系统

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/register` | 注册 | 否 |
| POST | `/api/login` | 登录 (支持用户名/邮箱) | 否 |
| GET | `/api/me` | 获取当前用户信息 | 是 |

#### 密码管理

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/password/forgot` | 发送重置 Token 到邮箱 | 否 |
| POST | `/api/password/forgot-code` | 发送 6 位验证码到邮箱 (推荐) | 否 |
| POST | `/api/password/reset` | 用 Token 重置密码 | 否 |
| POST | `/api/password/reset-by-code` | 用验证码重置密码 (推荐) | 否 |
| POST | `/api/password/change` | 已登录用户改密 | 是 |

#### 核心业务

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/upload` | 上传视频/图片 → 创建任务 | 是 |
| GET | `/api/status?task_id=N` | 查询任务状态 | 是 |
| GET | `/api/download?task_id=N` | 获取处理完成的下载链接 | 是 |
| GET | `/api/tasks` | 分页查询任务列表 | 是 |
| POST | `/api/tasks/{id}/cancel` | 取消任务 | 是 |
| POST | `/api/tasks/{id}/retry` | 重试失败任务 | 是 |
| DELETE | `/api/tasks/{id}` | 删除任务及文件 | 是 |

#### 系统

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/ping` | 简单健康检查 | 否 |
| GET | `/api/health` | 详细健康检查 (DB/Redis/Storage) | 否 |
| GET | `/api/test` | Unity 联通测试 | 否 |

#### 内部接口 (AI Worker 回调)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/internal/task_callback` | Worker 上报任务状态 | X-Internal-Token |

### 请求/响应示例

#### 注册

```
POST /api/register
Content-Type: application/json

{
  "username": "testuser",
  "email": "test@example.com",
  "password": "123456"
}

→ 200 { "access_token": "eyJ...", "token_type": "bearer" }
```

#### 登录

```
POST /api/login
Content-Type: application/json

{
  "identifier": "testuser",
  "password": "123456"
}

→ 200 { "access_token": "eyJ...", "token_type": "bearer" }
```

#### 上传视频

```
POST /api/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <video.mp4>
params_json: {"style": "anime", "strength": 0.8}

→ 200 { "code": 0, "data": { "task_id": 1, "params": {...} } }
```

#### 查询状态

```
GET /api/status?task_id=1
Authorization: Bearer <token>

→ 200 {
  "task_id": 1,
  "status": "processing",
  "progress": 45,
  "params": {"style": "anime"},
  "error_msg": null,
  "created_at": "2026-03-30T10:00:00",
  "updated_at": "2026-03-30T10:00:05"
}
```

#### 下载结果

```
GET /api/download?task_id=1
Authorization: Bearer <token>

→ 200 { "download_url": "http://host/static/videos/out/1/abc.mp4" }
```

#### 任务列表

```
GET /api/tasks?page=1&page_size=10&status=completed&sort=created_desc
Authorization: Bearer <token>

→ 200 {
  "items": [...],
  "page": 1, "page_size": 10, "total": 25, "pages": 3,
  "self_url": "...", "next_url": "...", "prev_url": null
}
```

### 任务状态流转

```
queued → processing → completed
                   → failed → (retry) → queued
       → (cancel)  → failed
```

### 错误码

| HTTP 状态 | 含义 |
|-----------|------|
| 400 | 参数错误 |
| 401 | 未认证 / Token 无效 |
| 403 | 无权限 (非本人任务) |
| 404 | 资源不存在 |
| 409 | 用户名/邮箱已存在 |
| 413 | 文件过大 |

## 后端 ↔ AI Worker 协议

### 任务数据格式 (Redis 队列)

```json
{
  "task_id": 1,
  "user_id": 1,
  "input_path": "videos/raw/1/abc123.mp4",
  "params": {
    "style": "anime",
    "strength": 0.8
  }
}
```

### 回调方式 (Worker → Backend)

Worker 通过 HTTP POST 回调通知后端状态更新：

```
POST http://backend:8000/internal/task_callback
X-Internal-Token: <INTERNAL_TOKEN>
Content-Type: application/json

{
  "task_id": 1,
  "status": "completed",
  "progress": 100,
  "output_path": "videos/out/1/result.mp4",
  "error_msg": null
}
```

### 状态流转要求

| 状态 | progress | output_path | error_msg |
|------|----------|-------------|-----------|
| queued | 0 | null | null |
| processing | 1-99 | null | null |
| completed | 100 | 必填 | null |
| failed | any | null | 必填 |

## 环境变量

参见 `.env.example` 获取完整配置说明。

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 路由入口
│   ├── models.py          # SQLAlchemy 模型 (User, Task)
│   ├── schemas.py         # Pydantic 请求/响应模型
│   ├── db.py              # 数据库连接
│   ├── auth.py            # JWT + bcrypt 认证
│   ├── storage.py         # 文件存储服务
│   ├── tasks.py           # 任务处理 + 入队逻辑
│   ├── queue.py           # Redis 队列辅助
│   ├── internal.py        # 内部回调路由
│   ├── mailer.py          # SMTP 邮件发送
│   ├── password_code.py   # Redis 验证码
│   └── logging_config.py  # 日志配置
├── worker.py              # Redis 队列消费者
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```
