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
