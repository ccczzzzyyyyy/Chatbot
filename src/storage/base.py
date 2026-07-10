"""存储后端抽象基类 —— 定义统一的 CRUD 接口规范"""

from abc import ABC, abstractmethod
from typing import Optional

from src.models.schemas import Message, Preset, Session, User, UserConfig


class StorageBackend(ABC):
    """存储后端抽象基类，所有存储实现必须继承此类"""

    # ── User CRUD ──────────────────────────────────────────

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """创建用户，返回带 id 的 User"""
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        ...

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        ...

    @abstractmethod
    async def list_users(self) -> list[User]:
        """列出所有用户"""
        ...

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """更新用户信息"""
        ...

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """删除用户及其关联数据，返回是否成功"""
        ...

    # ── Session CRUD ───────────────────────────────────────

    @abstractmethod
    async def create_session(self, session: Session) -> Session:
        """创建会话"""
        ...

    @abstractmethod
    async def get_session_by_id(self, session_id: int) -> Optional[Session]:
        """根据 ID 获取会话"""
        ...

    @abstractmethod
    async def list_sessions_by_user(self, user_id: int) -> list[Session]:
        """列出用户的所有会话"""
        ...

    @abstractmethod
    async def update_session(self, session: Session) -> Session:
        """更新会话"""
        ...

    @abstractmethod
    async def delete_session(self, session_id: int) -> bool:
        """删除会话及其所有消息"""
        ...

    # ── Message CRUD ───────────────────────────────────────

    @abstractmethod
    async def create_message(self, message: Message) -> Message:
        """创建消息"""
        ...

    @abstractmethod
    async def list_messages_by_session(self, session_id: int) -> list[Message]:
        """列出会话的所有消息"""
        ...

    @abstractmethod
    async def search_messages(self, user_id: int, keyword: str) -> list[dict]:
        """在当前用户的所有会话中搜索消息，返回 [(message, session_title), ...]"""
        ...

    # ── Preset CRUD ────────────────────────────────────────

    @abstractmethod
    async def create_preset(self, preset: Preset) -> Preset:
        """创建预设"""
        ...

    @abstractmethod
    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        """根据 ID 获取预设"""
        ...

    @abstractmethod
    async def list_presets(self, user_id: Optional[int] = None) -> list[Preset]:
        """列出预设：user_id=None 返回所有（内置+该用户自定义），user_id 指定返回该用户的"""
        ...

    @abstractmethod
    async def update_preset(self, preset: Preset) -> Preset:
        """更新预设"""
        ...

    @abstractmethod
    async def delete_preset(self, preset_id: int) -> bool:
        """删除预设"""
        ...

    # ── UserConfig CRUD ────────────────────────────────────

    @abstractmethod
    async def set_user_config(self, config: UserConfig) -> UserConfig:
        """设置用户配置（存在则更新，不存在则插入）"""
        ...

    @abstractmethod
    async def get_user_config(self, user_id: int, key: str) -> Optional[str]:
        """获取用户配置值"""
        ...

    @abstractmethod
    async def list_user_configs(self, user_id: int) -> list[UserConfig]:
        """列出用户所有配置"""
        ...

    # ── Lifecycle ──────────────────────────────────────────

    @abstractmethod
    async def initialize(self) -> None:
        """初始化存储（建表等）"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        ...
