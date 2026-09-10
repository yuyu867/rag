# AI 智能营养师 Agent「小营」

基于 **LangGraph + FastAPI + Vue3** 的多模态 AI 智能营养师：用户用文字（可带食物图片）提问，Agent 自主调用工具（BMI 计算、营养知识检索、食物图片分析）收集资料，再由大模型综合成专业、带数据的饮食建议，通过 SSE 流式返回前端。

## ✨ 功能特性

- **用户系统**：注册 / 登录（JWT 鉴权，PBKDF2 密码哈希），内置默认管理员 `admin / admin`
- **会话历史**：左侧会话列表，多会话管理，历史对话持久化在 PostgreSQL，重启后可随时恢复
- **BMI 计算**：支持中文表达（`80kg`、`80公斤`、`80斤`、`175cm`、`1米75` 等），按中国标准分档（偏瘦 / 正常 / 超重 / 肥胖）
- **营养知识检索（RAG）**：内置约 65 条营养知识（食物 GI 值、慢性病饮食建议、营养常识、运动建议），基于 ChromaDB 向量检索
- **食物图片分析**：上传食物图片，视觉模型识别菜品并估算热量与营养成分
- **SSE 流式回复**：后端流式推送，前端逐段渲染
- **多轮记忆**：LangGraph Checkpointer 持久化 Agent 上下文，同一会话内多轮追问不丢上下文

## 🛠 技术栈

| 层 | 技术 |
|-----|------|
| 前端 | Vue3 + Element Plus + TypeScript + Vite + markdown-it |
| 后端 | Python FastAPI + uvicorn |
| Agent 框架 | LangGraph（StateGraph） |
| LLM | 通义千问 qwen-plus（DashScope） |
| 视觉模型 | qwen3.7-plus（阿里云百炼） |
| Embedding | text-embedding-v2（DashScope） |
| 向量数据库 | ChromaDB |
| 数据库 | PostgreSQL（asyncpg + SQLAlchemy 2.0 async）：用户 / 会话 / 消息 |
| 鉴权 | JWT（PyJWT）+ PBKDF2 密码哈希 |
| 通信 | HTTP + SSE（sse-starlette） |

## 🏗 架构

```
Vue3 SPA  ──SSE──▶  FastAPI  ──▶  LangGraph Agent
     │                 │            ├─ LLM: qwen3.7-plus
     │  JWT 鉴权        │            ├─ Vision: qwen3.7-plus
     │                 │            ├─ Embedding: text-embedding-v3
 PostgreSQL ◀──────────┘            ├─ Vector Store: ChromaDB
 users / conversations / messages   └─ Tools: BMI / 知识检索 / 图片分析
```

### Agent 工作流

```
用户输入(文字+可选图片)
        │
   [prepare]   ← 正则提取 BMI 参数 + 检索知识库 + 分析图片（无需 LLM 分类）
        │
   [generate]  ← 唯一一次 LLM 调用：综合上下文生成最终回复
        │
     输出回复（SSE）
```

## 🚀 快速开始

### 0. 准备 PostgreSQL

需要一个 PostgreSQL 实例，并创建数据库：

```sql
CREATE DATABASE rag_nutrition;
```

在 `backend/.env` 中配置连接串（用户名/密码换成你自己的）：

```
DATABASE_URL=postgresql+asyncpg://postgres:你的密码@localhost:5432/rag_nutrition
JWT_SECRET=换成一段随机长字符串
```

启动后端时自动建表（users / conversations / messages），并创建默认管理员 **admin / admin**。

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
# 复制环境变量模板并填入真实密钥
cp .env.example .env        # Windows: copy .env.example .env
python main.py
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:3000，用默认账户 `admin / admin` 登录即可对话。

### 3. Docker 一键部署（可选）

在**项目根目录**创建 `.env`：

```
OPENAI_API_KEY=你的百炼Key
POSTGRES_PASSWORD=数据库密码
JWT_SECRET=一段随机长字符串
```

然后：

```bash
docker compose up -d --build
# 访问 http://localhost:8080（前端 nginx + 后端 + PostgreSQL 三容器）
```

- `pg_data` 卷存数据库，`app_data` 卷存向量库与 Agent 记忆，重建容器不丢数据
- 改端口：`.env` 里加 `FRONTEND_PORT=80`；改限流：`CHAT_RATE_LIMIT=每分钟次数`

## 🔐 安全机制

- **鉴权**：JWT（默认 7 天），PBKDF2-SHA256（24 万次迭代 + 随机盐）存密码
- **限流**：`/api/chat` 默认 10 次/分钟/用户（`CHAT_RATE_LIMIT` 可调），上传 20 次/分钟，超限返回 429
- **上传校验**：仅 jpg/png/webp、≤5MB、校验文件魔数（防伪装文件），前后端双重校验
- **CORS**：默认仅放行本地开发端口，生产通过 `CORS_ORIGINS=https://your-domain.com` 配置
- **默认账户**：admin/admin 仅用于首次登录，请登录后立即在左上角「改密」修改

## 🔌 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录，返回 JWT |
| GET | /api/auth/me | 当前用户信息 |
| POST | /api/auth/change-password | 修改密码 |
| GET | /api/conversations | 会话列表 |
| POST | /api/conversations | 创建会话 |
| DELETE | /api/conversations/{id} | 删除会话（级联删消息） |
| GET | /api/conversations/{id}/messages | 会话历史消息 |
| POST | /api/chat | 对话，SSE 流式回复（需登录） |
| POST | /api/chat/upload | 上传图片，返回 base64 |

> 除注册/登录/健康检查外，所有接口都需要 `Authorization: Bearer <token>`。

## 📁 目录结构

```
.
├── backend/            # FastAPI + LangGraph 后端
│   ├── main.py         # 入口 + SSE + 建表/管理员种子
│   ├── config.py       # 集中配置（模型/密钥/数据库连接）
│   ├── database.py     # PostgreSQL 异步引擎与会话
│   ├── models.py       # ORM：users / conversations / messages
│   ├── auth.py         # PBKDF2 哈希 + JWT + 登录态依赖
│   ├── routers.py      # 注册/登录 + 会话管理路由
│   ├── agent/          # Agent 状态、工具、状态图
│   └── knowledge/      # 种子数据 + ChromaDB 向量库
├── frontend/           # Vue3 前端
│   └── src/
│       ├── api/        # SSE 客户端 + auth/conversations 接口
│       ├── stores/     # 登录态 / 会话列表状态
│       ├── views/      # 登录注册页
│       └── components/ # 聊天界面 + 会话侧边栏组件
└── docs/               # 设计文档与实现计划
```

## ⚠️ 说明

- **登录鉴权**：JWT 默认 7 天有效；JWT_SECRET 生产环境务必改成随机长字符串
- **两层持久化**：用户/会话/聊天记录在 PostgreSQL（展示与恢复）；Agent 多轮上下文在本地 SQLite checkpointer（LangGraph 记忆），高并发场景可换 PostgresSaver
- 密钥统一通过环境变量配置（见 `backend/.env.example`），**请勿提交 `.env`**
- 首次启动请用 admin 登录后尽快修改默认密码（或通过 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 环境变量自定义种子账户）

## 📄 License

[MIT](./LICENSE)
