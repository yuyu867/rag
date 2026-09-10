import re

from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from openai import OpenAI

import config
from agent.state import AgentState
from agent.tools import calculate_bmi, retrieve_knowledge, analyze_food_image


SYSTEM_PROMPT = """你是一位专业的AI营养师，名字叫"小营"。请用专业、友好的口吻回答用户。给出建议时引用具体数据。

你可以使用以下工具能力：
1. BMI计算 — 根据身高体重评估体重状况
2. 营养知识库 — 检索食物GI值、慢性病饮食建议、运动建议等
3. 食物图片分析 — 识别食物并估算营养成分

回答时请结合参考数据，给出具体可操作的建议。"""


def get_llm_client() -> OpenAI:
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


def _extract_bmi_params(text: str) -> tuple[float, float]:
    """从用户输入中用正则提取体重(kg)和身高(m)，无需LLM。"""
    weight, height = 0.0, 0.0

    # 体重: "80kg" "80公斤" "80千克" "80斤"
    w_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|公斤|千克|斤)', text)
    if w_match:
        w = float(w_match.group(1))
        weight = w / 2 if '斤' in w_match.group() else w

    # 身高: "1.75" "175cm" "175厘米" "1米75"
    h_cm = re.search(r'(\d+(?:\.\d+)?)\s*(?:cm|厘米)', text)
    h_m = re.search(r'(\d+)\.?(\d*)\s*(?:m|米)', text)
    h_combo = re.search(r'(\d+)\s*米\s*(\d+)', text)

    if h_cm:
        height = float(h_cm.group(1)) / 100
    elif h_combo:
        height = float(h_combo.group(1)) + float(h_combo.group(2)) / 100
    elif h_m:
        height = float(h_m.group(1)) + (float(h_m.group(2)) / 100 if h_m.group(2) else 0)

    # 单个数字如"175"可能是cm
    if height == 0:
        h_num = re.search(r'(?:身高|高)\s*(\d{2,3})(?!\s*(?:kg|公斤|斤))', text)
        if h_num:
            val = float(h_num.group(1))
            height = val / 100 if val > 3 else val

    return weight, height


def prepare(state: AgentState) -> dict:
    """准备上下文：正则提取BMI参数 + 检索知识库 + 分析图片（均不需要LLM分类）。"""
    user_input = state["user_input"]
    result = {
        # 每轮重置，避免上一轮的结果残留到本轮
        "bmi_result": None,
        "knowledge_results": [],
        "food_analysis": None,
    }

    # 1. 正则提取身高体重，直接算BMI（纯本地，毫秒级）
    weight, height = _extract_bmi_params(user_input)
    if weight > 0 and height > 0:
        result["bmi_result"] = calculate_bmi.invoke({"weight_kg": weight, "height_m": height})

    # 2. 检索知识库（ChromaDB embedding API，通常 < 1秒）
    try:
        kb_results = retrieve_knowledge.invoke({"query": user_input})
        result["knowledge_results"] = [kb_results] if isinstance(kb_results, str) else kb_results
    except Exception:
        result["knowledge_results"] = []

    # 3. 食物图片分析（仅当有图片时调用）
    image = state.get("image_base64")
    if image:
        try:
            result["food_analysis"] = analyze_food_image.invoke({"image_base64": image})
        except Exception:
            result["food_analysis"] = None

    return result


def _build_context(state: AgentState) -> str:
    """把工具结果拼成给 LLM 的参考资料。"""
    parts = []
    if state.get("bmi_result"):
        parts.append(f"[BMI计算结果]\n{state['bmi_result']}")
    if state.get("knowledge_results"):
        parts.append("[知识库检索结果]\n" + "\n".join(str(r) for r in state["knowledge_results"]))
    if state.get("food_analysis"):
        parts.append(f"[食物图片分析]\n{state['food_analysis']}")
    return "\n\n".join(parts)


def generate_response(state: AgentState) -> dict:
    """综合上下文，流式生成最终回复（唯一一次 LLM 调用）。"""
    writer = get_stream_writer()
    context = _build_context(state)

    # 历史消息（含本轮用户消息）转 OpenAI 格式
    history = []
    for m in state["messages"]:
        role = "assistant" if getattr(m, "type", "") == "ai" else "user"
        content = m.content if isinstance(m.content, str) else str(m.content)
        history.append({"role": role, "content": content})

    # 把参考资料追加到最后一轮用户消息
    if context:
        if history and history[-1]["role"] == "user":
            history[-1]["content"] += (
                f"\n\n参考资料：\n{context}\n\n请综合以上信息，给出专业、全面的回答。"
            )
        else:
            history.append({"role": "user", "content": f"参考资料：\n{context}"})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    client = get_llm_client()
    stream = client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=messages,
        max_tokens=config.LLM_MAX_TOKENS,
        stream=True,
    )

    full_text = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            full_text += token
            writer(token)  # 逐个 token 流式输出

    return {"messages": [AIMessage(content=full_text)], "final_response": full_text}


def create_agent(checkpointer=None):
    """构造 Agent 图。checkpointer 为 None 时退回内存版（MemorySaver）。"""
    graph = StateGraph(AgentState)
    graph.add_node("prepare", prepare)
    graph.add_node("generate", generate_response)

    graph.set_entry_point("prepare")
    graph.add_edge("prepare", "generate")
    graph.add_edge("generate", END)

    if checkpointer is None:
        checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
