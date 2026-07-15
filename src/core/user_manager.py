"""用户管理器 —— 创建/切换/删除用户"""

import logging
from typing import Optional

from src.models.schemas import User
from src.storage.base import StorageBackend

logger = logging.getLogger("langchain_chat")


class UserManager:
    """用户管理业务逻辑"""

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage
        self._current_user: Optional[User] = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    async def create_user(self, username: str) -> User:
        """创建新用户，重名则报错"""
        existing = await self._storage.get_user_by_username(username)
        if existing:
            raise ValueError(f"用户名 '{username}' 已存在，请更换用户名")

        user = User(username=username)
        user = await self._storage.create_user(user)
        logger.info("创建用户: id=%d, username=%s", user.id, username)
        return user

    async def switch_user(self, username: str) -> User:
        """切换到指定用户"""
        user = await self._storage.get_user_by_username(username)
        if not user:
            raise ValueError(f"用户 '{username}' 不存在")
        self._current_user = user
        return user

    def set_current_user(self, user: Optional[User]) -> None:
        """设置当前登录用户（不查库，直接赋值，用于首次创建用户后的自动登录）"""
        self._current_user = user

    async def delete_user(self, username: str) -> bool:
        """删除用户及其所有关联数据"""
        user = await self._storage.get_user_by_username(username)
        if not user:
            raise ValueError(f"用户 '{username}' 不存在")

        # 如果删除的是当前登录用户，清除当前用户
        if self._current_user and self._current_user.id == user.id:
            self._current_user = None

        logger.info("删除用户: username=%s, id=%d", username, user.id)
        return await self._storage.delete_user(user.id)

    async def list_users(self) -> list[User]:
        """列出所有用户"""
        return await self._storage.list_users()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名查找用户"""
        return await self._storage.get_user_by_username(username)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 查找用户"""
        return await self._storage.get_user_by_id(user_id)

    async def update_user(self, user: User) -> User:
        """更新用户信息"""
        updated = await self._storage.update_user(user)
        if self._current_user and self._current_user.id == user.id:
            self._current_user = updated
        return updated
