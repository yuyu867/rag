"""ChromaDB 向量库封装。

Embedding 通过「OpenAI 兼容协议」调用阿里云百炼 MaaS 端点，
与文本 LLM / 视觉模型共用同一个 API Key，避免双 provider 不一致。
"""
import os

from langchain_chroma import Chroma
from openai import OpenAI

import config
from knowledge.seed_data import NUTRITION_SEEDS


class MaaSEmbeddings:
    """OpenAI 兼容 embedding 适配器（embed_documents / embed_query 接口）。"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class KnowledgeBase:
    _instance: "KnowledgeBase | None" = None

    def __init__(self):
        self.embeddings = MaaSEmbeddings(
            api_key=config.EMBEDDING_API_KEY,
            base_url=config.EMBEDDING_BASE_URL,
            model=config.EMBEDDING_MODEL,
        )
        self._load_or_create()

    @classmethod
    def get_instance(cls) -> "KnowledgeBase":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_or_create(self):
        persist_dir = config.CHROMA_PERSIST_DIR
        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            self.vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings,
                collection_name=config.CHROMA_COLLECTION,
            )
        else:
            os.makedirs(persist_dir, exist_ok=True)
            self.vectorstore = Chroma.from_texts(
                texts=NUTRITION_SEEDS,
                embedding=self.embeddings,
                persist_directory=persist_dir,
                collection_name=config.CHROMA_COLLECTION,
            )

    def search(self, query: str, k: int = 3) -> list[str]:
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
