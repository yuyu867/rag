"""认证模块：PBKDF2 密码哈希 + JWT 签发/校验 + FastAPI 登录态依赖。

- 密码使用标准库 hashlib.pbkdf2_hmac（SHA-256，24 万次迭代 + 随机盐），不存明文
- 登录态用 JWT（HS256，7 天有效），前端放 localStorage，请求带 Authorization: Bearer
"""
import hashlib
import hmac
import os
import time

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 天

PBKDF2_ITERATIONS = 240_000

# auto_error=False：未带 token 时返回 None，由依赖统一抛 401
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """格式：pbkdf2_sha256$迭代次数$盐(hex)$哈希(hex)"""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, hash_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": int(time.time()) + JWT_EXPIRE_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI 依赖：从 Authorization: Bearer 解析当前用户。"""
    if credentials is None:
        raise HTTPException(status_code=401, detail="未登录")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的登录凭证")

    user = (
        await db.execute(select(User).where(User.id == int(payload.get("sub", 0))))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user
