"""集中配置：统一管理 API Key、模型名与服务地址。

所有敏感信息与模型参数都从这里读取环境变量，避免散落在各模块硬编码。
环境变量示例见 backend/.env.example。
"""
import os

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# 阿里云百炼 MaaS 兼容端点（实际部署，兼容 OpenAI 协议）
_DEFAULT_MAAS_BASE_URL = (
    "https://ws-dhhwq9r77kravo0p.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)

# ============ 文本 LLM（对话回复） ============
# Key 优先级：LLM_API_KEY > DASHSCOPE_API_KEY > OPENAI_API_KEY
LLM_API_KEY = os.getenv(
    "LLM_API_KEY",
    os.getenv("DASHSCOPE_API_KEY", os.getenv("OPENAI_API_KEY", "")),
)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", _DEFAULT_MAAS_BASE_URL)
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.7-plus")
LLM_MAX_TOKENS = _int("LLM_MAX_TOKENS", 10000)

# ============ 视觉模型（食物图片分析） ============
# Key 优先级：VISION_API_KEY > OPENAI_API_KEY
VISION_API_KEY = os.getenv("VISION_API_KEY", os.getenv("OPENAI_API_KEY", ""))
VISION_BASE_URL = os.getenv("VISION_BASE_URL", _DEFAULT_MAAS_BASE_URL)
VISION_MODEL = os.getenv("VISION_MODEL", "qwen3.7-plus")
VISION_MAX_TOKENS = _int("VISION_MAX_TOKENS", 8000)

# ============ Embedding（向量化） ============
# Key 优先级：EMBEDDING_API_KEY > DASHSCOPE_API_KEY > OPENAI_API_KEY
EMBEDDING_API_KEY = os.getenv(
    "EMBEDDING_API_KEY",
    os.getenv("DASHSCOPE_API_KEY", os.getenv("OPENAI_API_KEY", "")),
)
EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL", _DEFAULT_MAAS_BASE_URL)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

# ============ 向量库 ============
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "nutrition_kb")
RETRIEVE_TOP_K = _int("RETRIEVE_TOP_K", 3)
