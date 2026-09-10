"""路由：用户注册/登录 + 会话（历史对话）管理。

- /api/auth/*            注册、登录、当前用户信息
- /api/conversations/*   左侧会话列表的增删查 + 历史消息
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_db
from models import Conversation, Message, User

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
conv_router = APIRouter(prefix="/api/conversations", tags=["conversations"])


# ============ 认证 ============

class AuthRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


def _user_payload(user: User) -> dict:
    return {"id": user.id, "username": user.username}


@auth_router.post("/register")
async def register(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    exists = (
        await db.execute(select(User).where(User.username == req.username))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被占用")
    user = User(username=req.username, password_hash=hash_password(req.password))
    db.add(user)
    await db.commit()
    return {"token": create_token(user), "user": _user_payload(user)}


@auth_router.post("/login")
async def login(req: AuthRequest, db: AsyncSession = Depends(get_db)):
    user = (
        await db.execute(select(User).where(User.username == req.username))
    ).scalar_one_or_none()
    if user is None or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": create_token(user), "user": _user_payload(user)}


@auth_router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return _user_payload(user)


@auth_router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(req.new_password)
    await db.commit()
    return {"ok": True}


# ============ 会话管理 ============

class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)


def _conv_payload(c: Conversation) -> dict:
    return {
        "id": c.id,
        "thread_id": c.thread_id,
        "title": c.title,
        "updated_at": c.updated_at.isoformat(),
    }


@conv_router.get("")
async def list_conversations(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    rows = (
        await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
        )
    ).scalars().all()
    return [_conv_payload(c) for c in rows]


@conv_router.post("")
async def create_conversation(
    body: ConversationCreate | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    title = (body.title if body else None) or "新对话"
    conv = Conversation(user_id=user.id, thread_id=uuid.uuid4().hex, title=title)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return _conv_payload(conv)


@conv_router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    await db.delete(conv)  # messages 由 FK CASCADE 级联删除
    await db.commit()
    return {"ok": True}


@conv_router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv = await db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    rows = (
        await db.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.id)
        )
    ).scalars().all()
    return [
        {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at.isoformat()}
        for m in rows
    ]
