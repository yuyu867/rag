import base64
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent.graph import create_agent
from agent.state import AgentState
from auth import hash_password
from database import Base, SessionLocal, engine, get_db
from models import Conversation, Message, User
from rate_limit import CHAT_RATE_LIMIT, rate_limit
from routers import auth_router, conv_router

# 对话记忆持久化文件（sqlite checkpointer，保存 Agent 上下文），服务重启后记忆不丢
CHECKPOINT_DB = os.getenv("CHECKPOINT_DB_PATH", "./checkpoints.db")

DEFAULT_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

# 图片上传限制
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def _check_image(content: bytes, content_type: str | None) -> None:
    """校验上传图片的大小、类型与魔数，防止伪装文件与超大请求。"""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/webp 图片")
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="图片不能超过 5MB")
    ok_magic = (
        content[:3] == b"\xff\xd8\xff"  # jpeg
        or content[:8] == b"\x89PNG\r\n\x1a\n"  # png
        or (content[:4] == b"RIFF" and content[8:12] == b"WEBP")  # webp
    )
    if not ok_magic:
        raise HTTPException(status_code=400, detail="文件内容不是有效的图片")


async def init_db() -> None:
    """建表（不存在时）+ 确保默认管理员 admin/admin 存在。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        admin = (
            await db.execute(select(User).where(User.username == DEFAULT_ADMIN_USERNAME))
        ).scalar_one_or_none()
        if admin is None:
            db.add(User(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=hash_password(DEFAULT_ADMIN_PASSWORD),
            ))
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("JWT_SECRET", "dev-secret-change-me-in-production") == (
        "dev-secret-change-me-in-production"
    ):
        import logging
        logging.getLogger("uvicorn.error").warning(
            "JWT_SECRET 未设置，正在使用开发默认值——生产环境请在 .env 中配置随机长字符串"
        )
    await init_db()
    # AsyncSqliteSaver 需在运行中的事件循环内创建
    async with AsyncSqliteSaver.from_conn_string(CHECKPOINT_DB) as checkpointer:
        app.state.agent = create_agent(checkpointer)
        yield


app = FastAPI(title="AI 智能营养师", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(conv_router)

# CORS：从环境变量读取（逗号分隔），默认只放行本地前端开发端口
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    text: str
    image_base64: str | None = None
    conversation_id: int


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "AI营养师"}


@app.post("/api/chat/upload")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(rate_limit("upload", 20, 60)),
):
    content = await file.read()
    _check_image(content, file.content_type)
    encoded = base64.b64encode(content).decode("utf-8")
    return {"image_base64": encoded}


@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    user: User = Depends(rate_limit(*CHAT_RATE_LIMIT)),
    db: AsyncSession = Depends(get_db),
):
    # 会话归属校验：只能往自己的会话发消息
    conv = await db.get(Conversation, request.conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    thread_id = conv.thread_id

    # 用户消息先落库（即使后续生成失败也已保存）；首轮消息生成会话标题
    db.add(Message(conversation_id=conv.id, role="user", content=request.text))
    if conv.title == "新对话":
        conv.title = request.text[:20]
    await db.commit()

    # 每轮重置工具结果字段；messages 用 add_messages 追加（由 checkpointer 持久化）
    initial_state: AgentState = {
        "messages": [HumanMessage(content=request.text)],
        "user_input": request.text,
        "image_base64": request.image_base64,
        "bmi_result": None,
        "knowledge_results": [],
        "food_analysis": None,
        "final_response": "",
    }
    config = {"configurable": {"thread_id": thread_id}}
    agent = app.state.agent

    async def event_stream():
        full_text = ""
        error_text = ""
        try:
            async for token in agent.astream(initial_state, config=config, stream_mode="custom"):
                if token:
                    full_text += token
                    yield {"data": token}
        except Exception as e:
            error_text = f"[服务出错] {e}"
            yield {"data": error_text}
        finally:
            # 流结束后助手回复落库 + 刷新会话排序时间
            try:
                async with SessionLocal() as save_db:
                    content = full_text or error_text
                    if content:
                        save_db.add(Message(
                            conversation_id=conv.id, role="assistant", content=content
                        ))
                    saved_conv = await save_db.get(Conversation, conv.id)
                    if saved_conv:
                        saved_conv.updated_at = datetime.now(timezone.utc)
                    await save_db.commit()
            except Exception:
                pass  # 持久化失败不影响本次已流式返回的内容

    return EventSourceResponse(event_stream())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
