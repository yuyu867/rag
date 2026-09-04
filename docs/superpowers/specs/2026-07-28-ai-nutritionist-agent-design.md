# AI 智能营养师 Agent — 设计文档

## 概述

基于 LangChain + LangGraph + Vue3 的多模态 AI 智能营养师，能够自主调用工具（BMI 计算、营养知识检索、食物图片分析），通过多步推理给出个性化饮食建议。

## 技术栈

| 层 | 技术 |
|-----|------|
| 前端 | Vue3 + Element Plus |
| 后端 | Python FastAPI |
| Agent 框架 | LangGraph (StateGraph) |
| LLM | 通义千问 qwen-plus (DashScope) |
| 视觉模型 | qwen-vl-plus |
| Embedding | text-embedding-v2 (DashScope) |
| 向量数据库 | ChromaDB |
| 通信 | HTTP + SSE 流式输出 |

## 架构

```
Vue3 SPA  ←── SSE 流式 ──→  FastAPI  ←──→  LangGraph Agent
                                               ├── LLM: qwen-plus
                                               ├── Vision: qwen-vl-plus
                                               ├── Embedding: text-embedding-v2
                                               ├── Vector Store: ChromaDB
                                               └── Tools: BMI计算 / 知识检索 / 食物图片分析
```

## Agent 工作流

```
用户输入(文字+可选图片)
        │
   [classify]   ← 意图分类
        │
   ┌────┼────┐
   ▼    ▼    ▼
[retrieve] [calc_bmi] [analyze_food]
   │    │    │
   └────┼────┘
        │
   [synthesize] ← 综合推理，流式生成回复
        │
     输出回复
```

## Agent 状态

```python
class AgentState(TypedDict):
    messages: list
    user_input: str
    image_base64: str | None
    bmi_result: str | None
    knowledge_results: list
    food_analysis: str | None
    final_response: str
```

## 三个工具

1. `calculate_bmi(weight_kg, height_m)` — 计算 BMI 并返回健康评估
2. `retrieve_knowledge(query)` — 从 ChromaDB 语义检索营养知识
3. `analyze_food_image(image_base64)` — 调用 qwen-vl-plus 识别食物并估算营养

## 知识库（内置种子数据，~65条）

- 食物 GI 值（~30 条）
- 常见慢性病饮食建议（~10 条）
- 营养常识（~15 条）
- 运动建议（~10 条）

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat | 发送消息，返回 SSE 流式回复 |
| POST | /api/chat/upload | 上传图片，返回 base64 |
| GET | /api/health | 健康检查 |

## 项目结构

```
.
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── agent/
│   │   ├── graph.py          # LangGraph 状态图
│   │   ├── tools.py          # 三个工具函数
│   │   └── state.py          # AgentState 定义
│   ├── knowledge/
│   │   ├── seed_data.py      # 种子数据
│   │   └── vector_store.py   # ChromaDB 操作
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── components/
│   │   │   ├── ChatWindow.vue
│   │   │   ├── ChatMessage.vue
│   │   │   └── ImageUpload.vue
│   │   └── api/
│   │       └── chat.ts
│   ├── package.json
│   └── vite.config.ts
└── docs/
```

## 环境变量

```
DASHSCOPE_API_KEY=sk-xxx
```

## 不包含的功能

- 用户登录/注册
- 对话历史持久化（仅会话级内存存储）
- 多轮对话记忆（本次仅单轮上下文）
- 移动端适配
