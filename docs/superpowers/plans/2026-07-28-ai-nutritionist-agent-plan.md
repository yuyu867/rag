# AI 智能营养师 Agent — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 LangGraph + FastAPI + Vue3 的多模态 AI 智能营养师，支持 BMI 计算、营养知识检索、食物图片分析。

**Architecture:** FastAPI 后端托管 LangGraph Agent，Agent 通过 3 个工具（BMI计算/知识检索/食物图片分析）自主决策推理，结果通过 SSE 流式推送到 Vue3 前端。

**Tech Stack:** Python FastAPI, LangChain, LangGraph, DashScope (qwen-plus / qwen-vl-plus / text-embedding-v2), ChromaDB, Vue3, Element Plus, Vite

## Global Constraints

- 不实现用户登录/注册
- 不持久化对话历史（会话级内存存储）
- 单轮上下文，不做多轮记忆
- 环境变量 DASHSCOPE_API_KEY 通过 .env 文件配置

---

### Task 1: 后端项目脚手架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/agent/__init__.py`
- Create: `backend/knowledge/__init__.py`

**Produces:** 项目依赖清单，后端目录结构就绪

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
langchain==0.3.14
langgraph==0.2.61
langchain-community==0.3.14
chromadb==0.5.23
dashscope==1.22.1
python-multipart==0.0.19
python-dotenv==1.0.1
pydantic==2.10.4
sse-starlette==2.2.1
```

- [ ] **Step 2: 创建 .env.example**

```
DASHSCOPE_API_KEY=your_api_key_here
```

- [ ] **Step 3: 创建 __init__.py 文件**

```python
# backend/agent/__init__.py (空文件)
```

```python
# backend/knowledge/__init__.py (空文件)
```

- [ ] **Step 4: 安装依赖**

Run: `cd "backend" && pip install -r requirements.txt`

---

### Task 2: Agent 状态定义

**Files:**
- Create: `backend/agent/state.py`

**Produces:** `AgentState` TypedDict，定义整个 Agent 工作流中各节点共享的数据结构

- [ ] **Step 1: 编写 state.py**

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_input: str
    image_base64: str | None
    intent: dict
    bmi_result: str | None
    knowledge_results: list[str]
    food_analysis: str | None
    final_response: str
```

- [ ] **Step 2: 验证导入**

Run: `cd "backend" && python -c "from agent.state import AgentState; print('OK')"`
Expected: 输出 `OK`

---

### Task 3: 种子数据

**Files:**
- Create: `backend/knowledge/seed_data.py`

**Produces:** `NUTRITION_SEEDS` 列表，包含 ~65 条中文营养知识

- [ ] **Step 1: 编写 seed_data.py**

```python
NUTRITION_SEEDS: list[str] = []

# === 食物 GI 值 (~30条) ===
GI_DATA = [
    "香蕉的GI值为52，属于低GI食物（≤55为低GI，56-69为中GI，≥70为高GI），可适量食用。",
    "白米饭的GI值为83，属于高GI食物，糖尿病患者应控制摄入量。",
    "苹果的GI值为36，属于低GI食物，富含果胶，有助于控制血糖。",
    "西瓜的GI值为72，属于高GI食物，但血糖负荷(GL)较低，少量食用问题不大。",
    "全麦面包的GI值为51，属于低GI食物，比白面包(75)更适合血糖控制人群。",
    "燕麦片的GI值为55，属于低GI食物，富含可溶性膳食纤维β-葡聚糖。",
    "土豆的GI值为78，属于高GI食物，但冷却后抗性淀粉增加，GI值有所下降。",
    "红薯的GI值为54，属于低GI食物，富含膳食纤维和维生素A。",
    "胡萝卜的GI值为39，属于低GI食物，可放心食用。",
    "南瓜的GI值为75，属于高GI食物，食用时需控制分量。",
    "葡萄的GI值为43，属于低GI食物，但含糖量不低，需适量。",
    "芒果的GI值为51，属于低GI食物，富含维生素C和维生素A。",
    "荔枝的GI值为79，属于高GI食物，含糖量高，建议每天不超过10颗。",
    "橙子的GI值为43，属于低GI食物，富含维生素C。",
    "猕猴桃的GI值为52，属于低GI食物，富含维生素C和膳食纤维。",
    "樱桃的GI值为22，属于极低GI食物，适合血糖控制人群。",
    "面条（精制小麦）的GI值为82，属于高GI食物。",
    "意大利面的GI值为49，属于低GI食物，因为硬质小麦结构致密消化慢。",
    "绿豆的GI值为27，属于低GI食物，富含蛋白质和膳食纤维。",
    "红豆的GI值为26，属于低GI食物，适合做杂粮饭搭配。",
    "黄豆的GI值为18，属于极低GI食物，富含优质植物蛋白。",
    "玉米的GI值为55，属于低至中GI食物，富含膳食纤维。",
    "小米粥的GI值为71，属于高GI食物，煮得越久GI越高。",
    "糯米的GI值为87，属于高GI食物，糖尿病患者应尽量避免。",
    "花生的GI值为14，属于极低GI食物，但热量高需控制摄入量。",
    "酸奶（原味）的GI值为36，属于低GI食物，富含益生菌。",
    "牛奶的GI值为27，属于低GI食物，富含钙质。",
    "蜂蜜的GI值为58，属于中GI食物，天然糖分也需控制。",
    "苏打饼干的GI值为74，属于高GI食物。",
    "腰果的GI值为22，属于低GI食物，但热量高。",
]

# === 慢性病饮食建议 (~10条) ===
DISEASE_ADVICE = [
    "糖尿病患者应遵循'少食多餐'原则，每餐搭配蛋白质和膳食纤维来延缓血糖上升。",
    "高血脂患者应减少饱和脂肪酸摄入，多吃深海鱼(富含Omega-3)、坚果和橄榄油。",
    "高尿酸/痛风患者应限制高嘌呤食物：动物内脏、海鲜、啤酒、浓肉汤。",
    "高血压患者应控制钠摄入（每天<6g盐），多摄入富含钾的食物如香蕉、土豆、菠菜。",
    "胃食管反流患者应避免空腹吃酸性水果（柑橘、柠檬）、辛辣食物和咖啡。",
    "骨质疏松人群应保证每日钙摄入800-1000mg，配合维生素D促进钙吸收。",
    "贫血人群应增加血红素铁摄入（瘦红肉、动物血），搭配维生素C促进铁吸收。",
    "便秘人群应每日摄入25-30g膳食纤维，同时保证充足饮水（1.5-2L/天）。",
    "减脂人群应制造300-500kcal的热量缺口，保证蛋白质摄入不低于1.2g/kg体重。",
    "消化功能弱的人群应选择易消化的食物如粥、蒸蛋、鱼肉，避免油炸和生冷食物。",
]

# === 营养常识 (~15条) ===
NUTRITION_BASICS = [
    "成年人每日推荐蛋白质摄入量为每公斤体重0.8-1.0g，运动人群可增至1.2-2.0g。",
    "1克蛋白质约含4千卡热量，1克碳水化合物约含4千卡，1克脂肪约含9千卡。",
    "人体每日总热量消耗(TDEE) = 基础代谢率(BMR) × 活动系数。",
    "早餐应占总热量的25-30%，午餐35-40%，晚餐25-30%，可加餐5-10%。",
    "膳食纤维推荐每日摄入量：女性25g，男性30g。",
    "反式脂肪酸每日摄入应不超过总热量的1%，主要来源为油炸食品和加工零食。",
    "每天应摄入至少5种不同颜色的蔬菜水果，以确保营养均衡。",
    "维生素D主要通过日晒合成，食物来源包括三文鱼、蛋黄和强化牛奶。",
    "铁元素分为血红素铁（动物来源，吸收率高）和非血红素铁（植物来源，吸收率低）。",
    "空腹不宜大量吃柿子(鞣酸)、山楂、香蕉(镁)和冷饮（刺激肠胃）。",
    "饭后半小时内不宜剧烈运动，以免影响消化。",
    "每天饮水推荐量为每公斤体重30-35ml，运动或高温环境下需适当增加。",
    "睡前2-3小时不宜大量进食，以免影响睡眠质量。",
    "咖啡因每日摄入不超过400mg（约2-3杯咖啡），过量可能引起心悸失眠。",
    "精制糖每日摄入应不超过总热量的10%，最好控制在5%以内。",
]

# === 运动建议 (~10条) ===
EXERCISE_ADVICE = [
    "每周应进行至少150分钟中等强度有氧运动或75分钟高强度有氧运动。",
    "BMI低于18.5的偏瘦人群应以力量训练为主增加肌肉量，不宜过多有氧运动。",
    "BMI在18.5-24的正常体重人群可结合有氧和力量训练，每周各2-3次。",
    "BMI在24-28的超重人群应以有氧运动为主(快走、游泳)，先减重再进行高强度训练。",
    "BMI超过28的肥胖人群应从低冲击运动开始(游泳、骑行)，保护关节。",
    "运动前应进行5-10分钟热身，运动后应进行5-10分钟拉伸。",
    "运动后30分钟内补充蛋白质有助于肌肉修复。",
    "早晨空腹运动不宜过度，容易低血糖。",
    "每周安排1-2天休息日，给身体恢复时间。",
    "运动中如出现头晕、胸闷、剧烈疼痛应立即停止并就医。",
]

for data in [GI_DATA, DISEASE_ADVICE, NUTRITION_BASICS, EXERCISE_ADVICE]:
    NUTRITION_SEEDS.extend(data)
```

- [ ] **Step 2: 验证数据**

Run: `cd "backend" && python -c "from knowledge.seed_data import NUTRITION_SEEDS; print(f'共{len(NUTRITION_SEEDS)}条种子数据')"`
Expected: `共65条种子数据`

---

### Task 4: 向量存储

**Files:**
- Create: `backend/knowledge/vector_store.py`

**Interfaces:**
- Produces: `KnowledgeBase` 类，提供 `search(query, k=3) -> list[str]` 方法

- [ ] **Step 1: 编写 vector_store.py**

```python
import os
import chromadb
from chromadb.config import Settings
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_chroma import Chroma
from knowledge.seed_data import NUTRITION_SEEDS


class KnowledgeBase:
    _instance: "KnowledgeBase | None" = None

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        self.embeddings = DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
        self._load_or_create()

    @classmethod
    def get_instance(cls) -> "KnowledgeBase":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_or_create(self):
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
                collection_name="nutrition_kb",
            )
        else:
            os.makedirs(self.persist_dir, exist_ok=True)
            self.vectorstore = Chroma.from_texts(
                texts=NUTRITION_SEEDS,
                embedding=self.embeddings,
                persist_directory=self.persist_dir,
                collection_name="nutrition_kb",
            )

    def search(self, query: str, k: int = 3) -> list[str]:
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
```

- [ ] **Step 2: 验证向量存储**

Run: `cd "backend" && python -c "import os; os.environ['DASHSCOPE_API_KEY']='test'; from knowledge.seed_data import NUTRITION_SEEDS; print(f'{len(NUTRITION_SEEDS)} seeds ready')"`
Expected: `65 seeds ready`

---

### Task 5: Agent 工具函数

**Files:**
- Create: `backend/agent/tools.py`

**Interfaces:**
- Produces: `calculate_bmi(weight_kg, height_m) -> str`, `retrieve_knowledge(query) -> str`, `analyze_food_image(image_base64) -> str`

- [ ] **Step 1: 编写 tools.py**

```python
import os
import base64
from langchain_core.tools import tool
from openai import OpenAI
from knowledge.vector_store import KnowledgeBase


@tool
def calculate_bmi(weight_kg: float, height_m: float) -> str:
    """计算BMI指数并根据中国标准给出评估。weight_kg=体重(公斤), height_m=身高(米)。"""
    if height_m <= 0 or weight_kg <= 0:
        return "错误：身高和体重必须大于0。"
    bmi = weight_kg / (height_m ** 2)
    if bmi < 18.5:
        level = "偏瘦"
        advice = "建议增加营养摄入，配合力量训练增加肌肉量。"
    elif bmi < 24:
        level = "正常"
        advice = "体重正常，请继续保持健康的饮食和运动习惯。"
    elif bmi < 28:
        level = "超重"
        advice = "建议控制饮食热量，每周进行至少150分钟有氧运动。"
    else:
        level = "肥胖"
        advice = "建议咨询医生或营养师制定减重计划，从低冲击运动开始。"
    return f"BMI={bmi:.1f}，属于{level}范围（中国标准）。{advice}"


@tool
def retrieve_knowledge(query: str) -> str:
    """从营养知识库中检索与query语义相关的营养学知识。query=自然语言查询。"""
    kb = KnowledgeBase.get_instance()
    results = kb.search(query, k=3)
    if not results:
        return "未找到相关知识。"
    return "\n".join(f"- {r}" for r in results)


@tool
def analyze_food_image(image_base64: str) -> str:
    """分析食物图片，识别菜品并估算营养成分。image_base64=图片的base64编码字符串。"""
    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        model="qwen-vl-plus",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
                {
                    "type": "text",
                    "text": "请识别这张图片中的食物，列出主要菜品，并估算其热量和主要营养成分（蛋白质、碳水化合物、脂肪），给出饮食建议。",
                },
            ],
        }],
        max_tokens=800,
    )
    return response.choices[0].message.content or "无法分析该图片。"
```

- [ ] **Step 2: 验证工具导入**

Run: `cd "backend" && python -c "from agent.tools import calculate_bmi, retrieve_knowledge, analyze_food_image; print('3 tools OK')"`
Expected: `3 tools OK`

---

### Task 6: LangGraph Agent 图

**Files:**
- Create: `backend/agent/graph.py`

**Interfaces:**
- Produces: `create_agent() -> CompiledStateGraph`
- 5 个节点: `classify_intent`, `run_bmi`, `run_knowledge`, `run_food_analysis`, `synthesize`

- [ ] **Step 1: 编写 graph.py**

```python
import os
import operator
from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from openai import OpenAI
from agent.state import AgentState
from agent.tools import calculate_bmi, retrieve_knowledge, analyze_food_image


SYSTEM_PROMPT = """你是一位专业的AI营养师，名字叫"小营"。你可以：
1. 计算用户的BMI指数
2. 检索营养知识库
3. 分析食物图片

请用专业、友好的口吻回答用户。给出建议时引用具体数据。"""


def get_llm_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )


def classify_intent(state: AgentState) -> dict:
    """分析用户意图，决定调用哪些工具。"""
    client = get_llm_client()
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "system",
            "content": "分析用户意图，只返回JSON: {\"needs_bmi\": bool, \"needs_knowledge\": bool, \"needs_food_analysis\": bool}。规则：提到身高体重→needs_bmi；提到营养/食物/疾病咨询→needs_knowledge；有图片→needs_food_analysis。",
        }, {
            "role": "user",
            "content": state["user_input"],
        }],
        temperature=0,
        max_tokens=200,
    )
    content = response.choices[0].message.content.strip()
    import json
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"needs_bmi": False, "needs_knowledge": True, "needs_food_analysis": False}
    has_image = bool(state.get("image_base64"))
    return {"intent": {
        "needs_bmi": result.get("needs_bmi", False),
        "needs_knowledge": result.get("needs_knowledge", True),
        "needs_food_analysis": result.get("needs_food_analysis", False) and has_image,
    }}


def route_after_classify(state: AgentState) -> list[str]:
    """根据意图路由到工具节点。"""
    intent = state.get("intent", {})
    nodes = []
    if intent.get("needs_bmi"):
        nodes.append("run_bmi")
    if intent.get("needs_knowledge"):
        nodes.append("run_knowledge")
    if intent.get("needs_food_analysis"):
        nodes.append("run_food_analysis")
    return nodes or ["run_knowledge"]


def run_bmi(state: AgentState) -> dict:
    """从用户输入提取身高体重并计算BMI。"""
    user_input = state["user_input"]
    client = get_llm_client()
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[{
            "role": "system",
            "content": "从用户输入中提取体重(kg)和身高(m)，返回JSON: {\"weight_kg\": float, \"height_m\": float}。如果无法提取，返回 {\"weight_kg\": 0, \"height_m\": 0}。",
        }, {
            "role": "user",
            "content": user_input,
        }],
        temperature=0,
        max_tokens=100,
    )
    import json
    try:
        params = json.loads(response.choices[0].message.content.strip())
    except json.JSONDecodeError:
        params = {"weight_kg": 0, "height_m": 0}
    result = calculate_bmi.invoke({"weight_kg": params["weight_kg"], "height_m": params["height_m"]})
    return {"bmi_result": result}


def run_knowledge(state: AgentState) -> dict:
    """检索营养知识库。"""
    results = retrieve_knowledge.invoke({"query": state["user_input"]})
    return {"knowledge_results": [results] if isinstance(results, str) else results}


def run_food_analysis(state: AgentState) -> dict:
    """分析上传的食物图片。"""
    image = state.get("image_base64")
    if not image:
        return {"food_analysis": None}
    result = analyze_food_image.invoke({"image_base64": image})
    return {"food_analysis": result}


def synthesize(state: AgentState) -> dict:
    """综合所有工具结果，生成最终回复（流式）。"""
    context_parts = []
    if state.get("bmi_result"):
        context_parts.append(f"[BMI计算结果]\n{state['bmi_result']}")
    if state.get("knowledge_results"):
        context_parts.append(f"[知识库检索结果]\n" + "\n".join(str(r) for r in state["knowledge_results"]))
    if state.get("food_analysis"):
        context_parts.append(f"[食物图片分析]\n{state['food_analysis']}")
    context = "\n\n".join(context_parts) if context_parts else "无工具调用结果"

    client = get_llm_client()
    response = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"用户问题：{state['user_input']}\n\n参考资料：\n{context}\n\n请综合以上信息，给出专业、全面的回答。如需用到具体数据请引用。"},
        ],
        stream=True,
        max_tokens=1000,
    )
    full_text = ""
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            full_text += chunk.choices[0].delta.content
    return {"final_response": full_text}


def create_agent():
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("run_bmi", run_bmi)
    graph.add_node("run_knowledge", run_knowledge)
    graph.add_node("run_food_analysis", run_food_analysis)
    graph.add_node("synthesize", synthesize)

    graph.set_entry_point("classify_intent")
    graph.add_conditional_edges("classify_intent", route_after_classify, {
        "run_bmi": "run_bmi",
        "run_knowledge": "run_knowledge",
        "run_food_analysis": "run_food_analysis",
    })
    graph.add_edge("run_bmi", "synthesize")
    graph.add_edge("run_knowledge", "synthesize")
    graph.add_edge("run_food_analysis", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()
```

- [ ] **Step 2: 验证 Agent 图编译**

Run: `cd "backend" && python -c "from agent.graph import create_agent; agent = create_agent(); print('Agent compiled OK')"`
Expected: `Agent compiled OK`

---

### Task 7: FastAPI 入口

**Files:**
- Create: `backend/main.py`

**Interfaces:**
- Produces: FastAPI app，3 个端点
  - `GET /api/health` → `{"status": "ok"}`
  - `POST /api/chat` → SSE 流式输出（sse-starlette）
  - `POST /api/chat/upload` → `{"image_base64": str}`

- [ ] **Step 1: 编写 main.py**

```python
import os
import base64
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.graph import create_agent
from agent.state import AgentState
from langchain_core.messages import HumanMessage

app = FastAPI(title="AI 智能营养师")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = create_agent()


class ChatRequest(BaseModel):
    text: str
    image_base64: str | None = None


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AI营养师"}


@app.post("/api/chat/upload")
async def upload_image(file: UploadFile = File(...)):
    content = await file.read()
    encoded = base64.b64encode(content).decode("utf-8")
    return {"image_base64": encoded}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    initial_state: AgentState = {
        "messages": [HumanMessage(content=request.text)],
        "user_input": request.text,
        "image_base64": request.image_base64,
        "intent": {},
        "bmi_result": None,
        "knowledge_results": [],
        "food_analysis": None,
        "final_response": "",
    }

    async def event_stream():
        for event in agent.stream(initial_state, stream_mode="values"):
            final = event.get("final_response", "")
            if final:
                yield {"data": final}
                break

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 2: 启动后端验证**

Run: `cd "backend" && timeout 5 python main.py 2>&1 || true`
Expected: 服务启动无报错

---

### Task 8: 前端项目脚手架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/vite-env.d.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "ai-nutritionist-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.13",
    "element-plus": "^2.9.1",
    "@element-plus/icons-vue": "^2.3.1",
    "markdown-it": "^14.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.2.1",
    "typescript": "~5.7.2",
    "vite": "^6.0.5",
    "vue-tsc": "^2.2.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 3: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI 智能营养师 - 小营</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 4: 创建 main.ts**

```typescript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'

const app = createApp(App)
app.use(ElementPlus)
app.mount('#app')
```

- [ ] **Step 5: 创建 tsconfig 文件**

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "src/vite-env.d.ts"]
}
```

```json
// tsconfig.node.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 6: 创建 vite-env.d.ts**

```typescript
/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}
```

- [ ] **Step 7: 安装前端依赖**

Run: `cd "frontend" && npm install`

---

### Task 9: 前端 API 客户端

**Files:**
- Create: `frontend/src/api/chat.ts`

**Produces:** `sendMessage(text, imageBase64?)` → SSE 流式响应，`uploadImage(file)` → base64

- [ ] **Step 1: 编写 chat.ts**

```typescript
export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}

export async function uploadImage(file: File): Promise<string> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch('/api/chat/upload', { method: 'POST', body: formData })
  const data = await res.json()
  return data.image_base64
}

export async function* sendMessage(text: string, imageBase64?: string): AsyncGenerator<string> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, image_base64: imageBase64 || null }),
  })

  const reader = res.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        if (data === '[DONE]') return
        yield data
      }
    }
  }
}
```

---

### Task 10: Vue 组件

**Files:**
- Create: `frontend/src/components/ChatMessage.vue`
- Create: `frontend/src/components/ImageUpload.vue`
- Create: `frontend/src/components/ChatWindow.vue`

- [ ] **Step 1: ChatMessage.vue**

```vue
<template>
  <div :class="['message', role]">
    <div class="avatar">
      <el-avatar v-if="role === 'user'" :size="36" icon="UserFilled" />
      <el-avatar v-else :size="36" style="background-color: #67c23a">
        <span style="font-size:14px;color:#fff">营</span>
      </el-avatar>
    </div>
    <div class="content">
      <div class="text" v-html="renderedContent"></div>
      <img v-if="imageUrl" :src="imageUrl" class="uploaded-image" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

const props = defineProps<{
  role: 'user' | 'assistant'
  content: string
  imageUrl?: string
}>()

const md = new MarkdownIt({ breaks: true })

const renderedContent = computed(() => {
  if (props.role === 'assistant') {
    return md.render(props.content)
  }
  return props.content
})
</script>

<style scoped>
.message { display: flex; gap: 10px; margin-bottom: 20px; }
.message.user { flex-direction: row-reverse; }
.avatar { flex-shrink: 0; }
.content { max-width: 75%; }
.text { padding: 10px 14px; border-radius: 12px; line-height: 1.6; }
.user .text { background: #409eff; color: #fff; }
.assistant .text { background: #f5f5f5; color: #333; }
.assistant .text :deep(p) { margin: 4px 0; }
.assistant .text :deep(ul) { padding-left: 18px; }
.uploaded-image { max-width: 200px; border-radius: 8px; margin-top: 6px; }
</style>
```

- [ ] **Step 2: ImageUpload.vue**

```vue
<template>
  <div class="image-upload">
    <input ref="fileInput" type="file" accept="image/*" @change="handleFile" style="display:none" />
    <el-button :icon="PictureFilled" circle @click="$refs.fileInput.click()" title="上传食物图片" />
    <div v-if="preview" class="preview">
      <img :src="preview" />
      <el-button :icon="Close" circle size="small" @click="clearImage" class="remove-btn" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { PictureFilled, Close } from '@element-plus/icons-vue'

const emit = defineEmits<{ (e: 'image', base64: string): void; (e: 'clear'): void }>()

const fileInput = ref<HTMLInputElement>()
const preview = ref<string>()

async function handleFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    const base64 = (ev.target?.result as string).split(',')[1]
    preview.value = ev.target?.result as string
    emit('image', base64)
  }
  reader.readAsDataURL(file)
}

function clearImage() {
  preview.value = undefined
  emit('clear')
}
</script>

<style scoped>
.image-upload { display: flex; align-items: center; gap: 8px; }
.preview { position: relative; display: inline-block; }
.preview img { max-height: 80px; border-radius: 8px; }
.remove-btn { position: absolute; top: -8px; right: -8px; }
</style>
```

- [ ] **Step 3: ChatWindow.vue**

```vue
<template>
  <div class="chat-window">
    <div class="header">AI 智能营养师 - 小营</div>
    <div class="messages" ref="msgContainer">
      <ChatMessage v-for="(msg, i) in messages" :key="i" v-bind="msg" />
      <div v-if="loading" class="typing">小营正在思考...</div>
    </div>
    <div class="input-area">
      <ImageUpload @image="onImage" @clear="imageBase64 = undefined" />
      <el-input
        v-model="input"
        placeholder="输入你的问题，例如：身高175体重80kg，高血糖前期能吃香蕉吗？"
        @keyup.enter="handleSend"
        :disabled="loading"
      />
      <el-button type="primary" @click="handleSend" :disabled="loading || !input.trim()">
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import ChatMessage from './ChatMessage.vue'
import ImageUpload from './ImageUpload.vue'
import { sendMessage, type ChatMessage as Msg } from '../api/chat'

const messages = ref<(Msg & { imageUrl?: string })[]>([])
const input = ref('')
const loading = ref(false)
const imageBase64 = ref<string>()
const msgContainer = ref<HTMLElement>()

function onImage(b64: string) {
  imageBase64.value = b64
}

async function handleSend() {
  const text = input.value.trim()
  if (!text || loading.value) return

  const userMsg: Msg & { imageUrl?: string } = { role: 'user', content: text }
  if (imageBase64.value) {
    userMsg.imageUrl = `data:image/jpeg;base64,${imageBase64.value}`
  }
  messages.value.push(userMsg)
  input.value = ''
  loading.value = true

  await nextTick()
  scrollToBottom()

  const assistantMsg: Msg & { imageUrl?: string } = { role: 'assistant', content: '' }
  messages.value.push(assistantMsg)

  try {
    let fullText = ''
    for await (const chunk of sendMessage(text, imageBase64.value)) {
      fullText += chunk
      assistantMsg.content = fullText
      await nextTick()
      scrollToBottom()
    }
  } catch (e) {
    assistantMsg.content = '抱歉，服务暂时不可用，请稍后重试。'
  }

  imageBase64.value = undefined
  loading.value = false
}

function scrollToBottom() {
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-window {
  max-width: 800px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column;
}
.header { padding: 16px; text-align: center; font-size: 18px; font-weight: bold;
  background: #67c23a; color: #fff; }
.messages { flex: 1; overflow-y: auto; padding: 20px; }
.input-area { display: flex; gap: 8px; padding: 12px 20px; border-top: 1px solid #eee;
  background: #fff; align-items: center; }
.typing { color: #999; font-size: 13px; padding: 8px 0; }
</style>
```

---

### Task 11: App.vue 整合

**Files:**
- Create: `frontend/src/App.vue`

- [ ] **Step 1: 编写 App.vue**

```vue
<template>
  <div id="app">
    <ChatWindow />
  </div>
</template>

<script setup lang="ts">
import ChatWindow from './components/ChatWindow.vue'
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
#app { background: #f0f2f5; }
</style>
```

---

### Task 12: 验证与集成测试

- [ ] **Step 1: 启动后端**

Run: `cd "backend" && python main.py`

- [ ] **Step 2: 测试健康检查**

Run: `curl http://localhost:8000/api/health`
Expected: `{"status":"ok","service":"AI营养师"}`

- [ ] **Step 3: 测试聊天接口**

Run:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"身高170体重65kg，BMI是多少？"}'
```
Expected: SSE 流式输出营养师回复

- [ ] **Step 4: 启动前端**

Run: `cd "frontend" && npm run dev`

- [ ] **Step 5: 浏览器访问**

打开 `http://localhost:3000`，输入问题测试完整流程
