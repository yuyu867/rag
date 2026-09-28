"""ChromaDB 向量库封装。

Embedding 通过「OpenAI 兼容协议」调用阿里云百炼 MaaS 端点，
与文本 LLM / 视觉模型共用同一个 API Key，避免双 provider 不一致。
"""
import os

from langchain_chroma import Chroma
from openai import OpenAI

import config
from knowledge.seed_data import NUTRITION_SEEDS

# 种子内容（含食物成分数据）变化时递增此值，服务启动时自动重建向量库
KB_VERSION = "3"
EMBED_BATCH_SIZE = 10  # 阿里云百炼 text-embedding-v3 单次 batch 上限为 10


class MaaSEmbeddings:
    """OpenAI 兼容 embedding 适配器（embed_documents / embed_query 接口）。"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # 分批请求，避免单次 input 数量超过 API 上限
        out: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH_SIZE):
            out.extend(self._embed_batch(texts[i:i + EMBED_BATCH_SIZE]))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self._embed_batch([text])[0]


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
        marker = os.path.join(persist_dir, ".kb_version")
        exists = os.path.exists(persist_dir) and os.listdir(persist_dir)
        current = ""
        if exists and os.path.exists(marker):
            with open(marker, encoding="utf-8") as f:
                current = f.read().strip()

        if exists and current == KB_VERSION:
            self.vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings,
                collection_name=config.CHROMA_COLLECTION,
            )
            return

        # 首次创建或种子版本变化：先嵌入到临时 collection，成功后替换旧的，
        # 避免 embedding 失败（欠费/网络异常）时把已有向量库清空。
        os.makedirs(persist_dir, exist_ok=True)
        import chromadb

        client = chromadb.PersistentClient(path=persist_dir)
        tmp_name = config.CHROMA_COLLECTION + "_tmp"
        try:
            client.delete_collection(tmp_name)
        except Exception:
            pass  # 残留临时 collection 不存在则忽略

        # 这一步是唯一可能因网络/欠费失败的环节，失败时旧 collection 不受影响
        Chroma.from_texts(
            texts=NUTRITION_SEEDS,
            embedding=self.embeddings,
            persist_directory=persist_dir,
            collection_name=tmp_name,
        )

        # 嵌入成功：删除旧 collection，把临时 collection 改名为正式名
        try:
            client.delete_collection(config.CHROMA_COLLECTION)
        except Exception:
            pass
        try:
            client.get_collection(tmp_name).modify(name=config.CHROMA_COLLECTION)
        except Exception:
            # 部分 chromadb 版本不支持改名，退回为直接删除临时集合后重建
            client.delete_collection(tmp_name)
            Chroma.from_texts(
                texts=NUTRITION_SEEDS,
                embedding=self.embeddings,
                persist_directory=persist_dir,
                collection_name=config.CHROMA_COLLECTION,
            )

        self.vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings,
            collection_name=config.CHROMA_COLLECTION,
        )
        with open(marker, "w", encoding="utf-8") as f:
            f.write(KB_VERSION)

    def search(self, query: str, k: int = 3) -> list[str]:
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
