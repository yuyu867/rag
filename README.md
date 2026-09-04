# AI 智能营养师 Agent「小营」

基于 **LangGraph + FastAPI + Vue3** 的多模态 AI 智能营养师：用户用文字（可带食物图片）提问，Agent 自主调用工具（BMI 计算、营养知识检索、食物图片分析）收集资料，再由大模型综合成专业、带数据的饮食建议，通过 SSE 流式返回前端。

## ✨ 功能特性

- **BMI 计算**：支持中文表达（`80kg`、`80公斤`、`80斤`、`175cm`、`1米75` 等），按中国标准分档（偏瘦 / 正常 / 超重 / 肥胖）
- **营养知识检索（RAG）**：内置约 65 条营养知识（食物 GI 值、慢性病饮食建议、营养常识、运动建议），基于 ChromaDB 向量检索
- **食物图片分析**：上传食物图片，视觉模型识别菜品并估算热量与营养成分
- **SSE 流式回复**：后端流式推送，前端逐段渲染

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
| 通信 | HTTP + SSE（sse-starlette） |

## 🏗 架构

```
Vue3 SPA  ──SSE──▶  FastAPI  ──▶  LangGraph Agent
                                   ├─ LLM: qwen-plus
                                   ├─ Vision: qwen3.7-plus
                                   ├─ Embedding: text-embedding-v2
                                   ├─ Vector Store: ChromaDB
                                   └─ Tools: BMI / 知识检索 / 图片分析
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

打开 http://localhost:3000 即可对话。

## 🔌 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/health | 健康检查 |
| POST | /api/chat | 对话，SSE 流式回复 |
| POST | /api/chat/upload | 上传图片，返回 base64 |

## 📁 目录结构

```
.
├── backend/            # FastAPI + LangGraph 后端
│   ├── main.py         # 入口 + SSE
│   ├── agent/          # Agent 状态、工具、状态图
│   └── knowledge/      # 种子数据 + ChromaDB 向量库
├── frontend/           # Vue3 前端
│   └── src/
│       ├── api/        # SSE 客户端
│       └── components/ # 聊天界面组件
└── docs/               # 设计文档与实现计划
```

## ⚠️ 说明

- 当前为**单轮对话**：无多轮记忆、无登录注册、无对话历史持久化
- 密钥统一通过环境变量配置（见 `backend/.env.example`），**请勿提交 `.env`**

## 📄 License

[MIT](./LICENSE)
