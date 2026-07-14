"""文件系统存储后端 —— 使用 JSON 文件实现持久化"""

import asyncio
import json
import os
from datetime import datetime
from typing import Optional

from src.models.schemas import Message, Preset, Session, User, UserConfig
from src.storage.base import StorageBackend


class FileBackend(StorageBackend):
    """JSON 文件系统存储后端"""

    def __init__(self, data_dir: str = "data/file_storage") -> None:
        self._data_dir = data_dir
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """确保数据目录存在"""
        os.makedirs(self._data_dir, exist_ok=True)
        for subdir in ["users", "sessions", "messages", "presets", "configs"]:
            os.makedirs(os.path.join(self._data_dir, subdir), exist_ok=True)

    async def close(self) -> None:
        """无需特别关闭操作"""
        pass

    async def _next_id(self, entity: str) -> int:
        """生成自增 ID"""
        id_file = os.path.join(self._data_dir, f"{entity}_next_id")
        async with self._lock:
            if os.path.exists(id_file):
                with open(id_file, "r") as f:
                    current = int(f.read().strip())
            else:
                current = 0
            next_id = current + 1
            with open(id_file, "w") as f:
                f.write(str(next_id))
            return next_id

    def _read_json(self, filepath: str) -> Optional[dict]:
        """读取 JSON 文件"""
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, filepath: str, data: dict) -> None:
        """写入 JSON 文件"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def _delete_file(self, filepath: str) -> bool:
        """删除文件"""
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def _list_files(self, directory: str) -> list[dict]:
        """列出目录下所有 JSON 文件内容"""
        results = []
        if not os.path.exists(directory):
            return results
        for filename in sorted(os.listdir(directory)):
            if filename.endswith(".json"):
                data = self._read_json(os.path.join(directory, filename))
                if data:
                    results.append(data)
        return results

    # ── User CRUD ──────────────────────────────────────────

    async def create_user(self, user: User) -> User:
        user.id = await self._next_id("users")
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        self._write_json(
            os.path.join(self._data_dir, "users", f"{user.id}.json"),
            user.model_dump(),
        )
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        data = self._read_json(os.path.join(self._data_dir, "users", f"{user_id}.json"))
        return User(**data) if data else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        users = self._list_files(os.path.join(self._data_dir, "users"))
        for data in users:
            if data.get("username") == username:
                return User(**data)
        return None

    async def list_users(self) -> list[User]:
        users = self._list_files(os.path.join(self._data_dir, "users"))
        return [User(**d) for d in users]

    async def update_user(self, user: User) -> User:
        user.updated_at = datetime.now()
        self._write_json(
            os.path.join(self._data_dir, "users", f"{user.id}.json"),
            user.model_dump(),
        )
        return user

    async def delete_user(self, user_id: int) -> bool:
        return self._delete_file(os.path.join(self._data_dir, "users", f"{user_id}.json"))

    # ── Session CRUD ───────────────────────────────────────

    async def create_session(self, session: Session) -> Session:
        session.id = await self._next_id("sessions")
        session.created_at = datetime.now()
        session.updated_at = datetime.now()
        os.makedirs(os.path.join(self._data_dir, "sessions", str(session.user_id)), exist_ok=True)
        self._write_json(
            os.path.join(self._data_dir, "sessions", str(session.user_id), f"{session.id}.json"),
            session.model_dump(),
        )
        return session

    async def get_session_by_id(self, session_id: int) -> Optional[Session]:
        # 需要遍历所有用户的会话目录
        sessions_root = os.path.join(self._data_dir, "sessions")
        if not os.path.exists(sessions_root):
            return None
        for user_dir in os.listdir(sessions_root):
            filepath = os.path.join(sessions_root, user_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                data = self._read_json(filepath)
                return Session(**data) if data else None
        return None

    async def list_sessions_by_user(self, user_id: int) -> list[Session]:
        directory = os.path.join(self._data_dir, "sessions", str(user_id))
        sessions = self._list_files(directory)
        return sorted(
            [Session(**d) for d in sessions],
            key=lambda s: s.updated_at if s.updated_at else datetime.min,
            reverse=True,
        )

    async def update_session(self, session: Session) -> Session:
        session.updated_at = datetime.now()
        self._write_json(
            os.path.join(self._data_dir, "sessions", str(session.user_id), f"{session.id}.json"),
            session.model_dump(),
        )
        return session

    async def delete_session(self, session_id: int) -> bool:
        sessions_root = os.path.join(self._data_dir, "sessions")
        if not os.path.exists(sessions_root):
            return False
        for user_dir in os.listdir(sessions_root):
            filepath = os.path.join(sessions_root, user_dir, f"{session_id}.json")
            if os.path.exists(filepath):
                return self._delete_file(filepath)
        return False

    # ── Message CRUD ───────────────────────────────────────

    async def create_message(self, message: Message) -> Message:
        message.id = await self._next_id("messages")
        message.created_at = datetime.now()
        msg_dir = os.path.join(self._data_dir, "messages", str(message.session_id))
        os.makedirs(msg_dir, exist_ok=True)
        self._write_json(
            os.path.join(msg_dir, f"{message.id}.json"),
            message.model_dump(),
        )
        return message

    async def list_messages_by_session(self, session_id: int) -> list[Message]:
        directory = os.path.join(self._data_dir, "messages", str(session_id))
        messages = self._list_files(directory)
        return sorted(
            [Message(**d) for d in messages],
            key=lambda m: m.created_at if m.created_at else datetime.min,
        )

    async def search_messages(self, user_id: int, keyword: str) -> list[dict]:
        results = []
        # 获取该用户所有会话
        sessions = await self.list_sessions_by_user(user_id)
        for session in sessions:
            messages = await self.list_messages_by_session(session.id)
            for msg in messages:
                if keyword.lower() in msg.content.lower():
                    d = msg.model_dump()
                    d["session_title"] = session.title
                    results.append(d)
        return sorted(
            results,
            key=lambda m: m.get("created_at", datetime.min),
            reverse=True,
        )[:100]

    # ── Preset CRUD ────────────────────────────────────────

    async def create_preset(self, preset: Preset) -> Preset:
        preset.id = await self._next_id("presets")
        preset.created_at = datetime.now()
        preset.updated_at = datetime.now()
        self._write_json(
            os.path.join(self._data_dir, "presets", f"{preset.id}.json"),
            preset.model_dump(),
        )
        return preset

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        data = self._read_json(os.path.join(self._data_dir, "presets", f"{preset_id}.json"))
        return Preset(**data) if data else None

    async def list_presets(self, user_id: Optional[int] = None) -> list[Preset]:
        presets = self._list_files(os.path.join(self._data_dir, "presets"))
        result = [Preset(**d) for d in presets]
        if user_id is None:
            return result
        return [p for p in result if p.is_builtin or p.user_id == user_id]

    async def update_preset(self, preset: Preset) -> Preset:
        preset.updated_at = datetime.now()
        self._write_json(
            os.path.join(self._data_dir, "presets", f"{preset.id}.json"),
            preset.model_dump(),
        )
        return preset

    async def delete_preset(self, preset_id: int) -> bool:
        return self._delete_file(os.path.join(self._data_dir, "presets", f"{preset_id}.json"))

    # ── UserConfig CRUD ────────────────────────────────────

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        config.updated_at = datetime.now()
        cfg_dir = os.path.join(self._data_dir, "configs", str(config.user_id))
        os.makedirs(cfg_dir, exist_ok=True)
        self._write_json(
            os.path.join(cfg_dir, f"{config.key}.json"),
            config.model_dump(),
        )
        return config

    async def get_user_config(self, user_id: int, key: str) -> Optional[str]:
        data = self._read_json(
            os.path.join(self._data_dir, "configs", str(user_id), f"{key}.json")
        )
        return data["value"] if data else None

    async def list_user_configs(self, user_id: int) -> list[UserConfig]:
        configs = self._list_files(os.path.join(self._data_dir, "configs", str(user_id)))
        return [UserConfig(**d) for d in configs]
