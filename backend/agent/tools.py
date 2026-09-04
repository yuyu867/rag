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
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://ws-dhhwq9r77kravo0p.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    response = client.chat.completions.create(
        model="qwen3.7-plus",
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
        max_tokens=8000,
    )
    return response.choices[0].message.content or "无法分析该图片。"
