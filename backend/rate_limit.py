"""进程内滑动窗口限流（按用户维度）。

适用单进程部署；多副本/多 worker 部署时应换成 Redis 等共享存储。
通过环境变量可调：CHAT_RATE_LIMIT（默认 10 次/分钟/用户）。
"""
import os
import time
from collections import defaultdict, deque

from fastapi import Depends, HTTPException

from auth import get_current_user
from models import User


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


# 各接口的限流配置：(scope, max_calls, window_seconds)
CHAT_RATE_LIMIT = (
    "chat",
    _int_env("CHAT_RATE_LIMIT", 10),
    _int_env("CHAT_RATE_WINDOW_SECONDS", 60),
)

# 全部桶（含已过期的），定期清理避免内存无限增长
_buckets: dict[tuple[int, str], deque] = {}


def rate_limit(scope: str, max_calls: int, window_seconds: int):
    """FastAPI 依赖工厂：替换 get_current_user 使用，同时完成鉴权与限流。"""

    def dependency(user: User = Depends(get_current_user)) -> User:
        now = time.monotonic()
        key = (user.id, scope)
        q = _buckets.setdefault(key, deque())

        while q and q[0] <= now - window_seconds:
            q.popleft()
        if len(q) >= max_calls:
            raise HTTPException(
                status_code=429,
                detail=f"请求太频繁（每 {window_seconds} 秒最多 {max_calls} 次），请稍后再试",
            )
        q.append(now)

        # 惰性清理：桶数量过多时丢弃已过期的
        if len(_buckets) > 10_000:
            expired = [
                k
                for k, v in _buckets.items()
                if not v or v[-1] <= now - window_seconds
            ]
            for k in expired:
                _buckets.pop(k, None)
        return user

    return dependency
