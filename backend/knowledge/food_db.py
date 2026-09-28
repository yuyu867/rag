"""加载由 build_food_db.py 生成的食物成分数据。

- load_food_seeds(): 返回自然语言种子句列表（供向量库嵌入）。
- load_foods():     返回结构化食物记录列表（供精确查询/未来工具使用）。

数据文件若尚未生成则返回空列表，不影响服务启动。
"""
import json
import os

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "data")
SEEDS_PATH = os.path.join(DATA_DIR, "food_seeds.json")
COMP_PATH = os.path.join(DATA_DIR, "food_composition.json")


def load_food_seeds() -> list[str]:
    if not os.path.exists(SEEDS_PATH):
        return []
    try:
        with open(SEEDS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def load_foods() -> list[dict]:
    if not os.path.exists(COMP_PATH):
        return []
    try:
        with open(COMP_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
