"""路由：用户注册/登录 + 会话（历史对话）管理。

- /api/auth/*            注册、登录、当前用户信息
- /api/conversations/*   左侧会话列表的增删查 + 历史消息
"""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_token,
    get_current_admin,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_db
from models import Conversation, Message, User

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
conv_router = APIRouter(prefix="/api/conversations", tags=["conversations"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

PHONE_RE = re.compile(r"^1[3-9]\d{9}$")  # 中国大陆手机号
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")


# ============ 认证 ============

class AuthRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    phone: str = Field(min_length=11, max_length=11, pattern=r"^1[3-9]\d{9}$")
    email: str | None = Field(default=None, max_length=120)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "phone": user.phone,
        "email": user.email,
        "is_admin": user.is_admin,
    }


@auth_router.post("/register")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not PHONE_RE.match(req.phone):
        raise HTTPException(status_code=400, detail="请输入正确的 11 位手机号")
    if req.email and not EMAIL_RE.match(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    exists = (
        await db.execute(select(User).where(User.username == req.username))
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被占用")

    phone_taken = (
        await db.execute(select(User).where(User.phone == req.phone))
    ).scalar_one_or_none()
    if phone_taken:
        raise HTTPException(status_code=400, detail="该手机号已注册")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        phone=req.phone,
        email=req.email,
    )
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


# ============ 管理员：账号管理 ============

class AdminUpdateUser(BaseModel):
    """可更新的字段均可选，未传表示不修改。"""
    password: str | None = Field(default=None, min_length=6, max_length=128)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    email: str | None = Field(default=None, max_length=120)
    is_admin: bool | None = None


@admin_router.get("/users")
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    conv_count = (
        select(func.count(Conversation.id))
        .where(Conversation.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    rows = (
        await db.execute(
            select(User, conv_count.label("conversation_count")).order_by(User.id)
        )
    ).all()
    return [
        {
            **_user_payload(user),
            "created_at": user.created_at.isoformat(),
            "conversation_count": count,
        }
        for user, count in rows
    ]


@admin_router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    body: AdminUpdateUser,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    if body.password is not None:
        target.password_hash = hash_password(body.password)
    if body.phone is not None:
        if not PHONE_RE.match(body.phone):
            raise HTTPException(status_code=400, detail="手机号格式不正确")
        taken = (
            await db.execute(select(User).where(User.phone == body.phone, User.id != user_id))
        ).scalar_one_or_none()
        if taken:
            raise HTTPException(status_code=400, detail="该手机号已被其他用户使用")
        target.phone = body.phone
    if body.email is not None:
        if body.email and not EMAIL_RE.match(body.email):
            raise HTTPException(status_code=400, detail="邮箱格式不正确")
        target.email = body.email or None
    if body.is_admin is not None:
        if target.id == admin.id and body.is_admin is False:
            raise HTTPException(status_code=400, detail="不能取消自己的管理员权限")
        target.is_admin = body.is_admin

    await db.commit()
    return _user_payload(target)


@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    await db.delete(target)  # 会话/消息由 FK CASCADE 级联删除
    await db.commit()
    return {"ok": True}
