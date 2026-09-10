"""PostgreSQL 异步连接与会话管理（SQLAlchemy 2.0 async + asyncpg）。

连接串从环境变量 DATABASE_URL 读取，见 .env.example。
说明：uvicorn 在 Windows 上固定使用 ProactorEventLoop，psycopg 异步模式不支持，
因此选用兼容 Proactor 的 asyncpg 驱动。
"""
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# postgresql+asyncpg:// 用户名:密码@主机:端口/库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_nutrition",
)

engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

# expire_on_commit=False：commit 后对象属性仍可读（SSE 流内使用）
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


async def get_db():
    """FastAPI 依赖：每个请求一个数据库会话。"""
    async with SessionLocal() as session:
        yield session
