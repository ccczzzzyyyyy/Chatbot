"""SQLite 存储后端 —— 使用 aiosqlite 实现异步 CRUD"""

from typing import Optional

import aiosqlite

from src.models.schemas import Message, Preset, Session, User, UserConfig
from src.storage.base import StorageBackend


class SQLiteBackend(StorageBackend):
    """SQLite 异步存储后端"""

    def __init__(self, db_path: str = "data/sqlite/app.db") -> None:
        self._db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def initialize(self) -> None:
        """初始化数据库，创建所有表"""
        import os

        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self._db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                default_model TEXT DEFAULT 'gpt-4o-mini',
                default_preset_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT DEFAULT '新对话',
                model_name TEXT DEFAULT 'gpt-4o-mini',
                preset_id INTEGER,
                total_prompt_tokens INTEGER DEFAULT 0,
                total_completion_tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS presets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                system_prompt TEXT DEFAULT '',
                is_builtin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, key)
            );

            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_messages_content ON messages(content);
            CREATE INDEX IF NOT EXISTS idx_presets_user_id ON presets(user_id);
            """
        )
        await self._conn.commit()

    async def close(self) -> None:
        """关闭数据库连接"""
        if self._conn:
            await self._conn.close()
            self._conn = None

    def _ensure_conn(self) -> aiosqlite.Connection:
        """确保连接存在"""
        if self._conn is None:
            raise RuntimeError("数据库未初始化，请先调用 initialize()")
        return self._conn

    # ── User CRUD ──────────────────────────────────────────

    async def create_user(self, user: User) -> User:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "INSERT INTO users (username, default_model, default_preset_id) VALUES (?, ?, ?)",
            (user.username, user.default_model, user.default_preset_id),
        )
        await conn.commit()
        user.id = cursor.lastrowid
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return self._row_to_user(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return self._row_to_user(row) if row else None

    async def list_users(self) -> list[User]:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM users ORDER BY id")
        rows = await cursor.fetchall()
        return [self._row_to_user(r) for r in rows]

    async def update_user(self, user: User) -> User:
        conn = self._ensure_conn()
        await conn.execute(
            "UPDATE users SET username=?, default_model=?, default_preset_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (user.username, user.default_model, user.default_preset_id, user.id),
        )
        await conn.commit()
        return user

    async def delete_user(self, user_id: int) -> bool:
        conn = self._ensure_conn()
        cursor = await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await conn.commit()
        return cursor.rowcount > 0

    # ── Session CRUD ───────────────────────────────────────

    async def create_session(self, session: Session) -> Session:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "INSERT INTO sessions (user_id, title, model_name, preset_id) VALUES (?, ?, ?, ?)",
            (session.user_id, session.title, session.model_name, session.preset_id),
        )
        await conn.commit()
        session.id = cursor.lastrowid
        return session

    async def get_session_by_id(self, session_id: int) -> Optional[Session]:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        return self._row_to_session(row) if row else None

    async def list_sessions_by_user(self, user_id: int) -> list[Session]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_session(r) for r in rows]

    async def update_session(self, session: Session) -> Session:
        conn = self._ensure_conn()
        await conn.execute(
            """UPDATE sessions SET title=?, model_name=?, preset_id=?,
               total_prompt_tokens=?, total_completion_tokens=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                session.title,
                session.model_name,
                session.preset_id,
                session.total_prompt_tokens,
                session.total_completion_tokens,
                session.id,
            ),
        )
        await conn.commit()
        return session

    async def delete_session(self, session_id: int) -> bool:
        conn = self._ensure_conn()
        cursor = await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await conn.commit()
        return cursor.rowcount > 0

    # ── Message CRUD ───────────────────────────────────────

    async def create_message(self, message: Message) -> Message:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "INSERT INTO messages (session_id, role, content, prompt_tokens, completion_tokens) VALUES (?, ?, ?, ?, ?)",
            (message.session_id, message.role, message.content, message.prompt_tokens, message.completion_tokens),
        )
        await conn.commit()
        message.id = cursor.lastrowid
        return message

    async def list_messages_by_session(self, session_id: int) -> list[Message]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_message(r) for r in rows]

    async def search_messages(self, user_id: int, keyword: str) -> list[dict]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            """SELECT m.*, s.title as session_title
               FROM messages m
               JOIN sessions s ON m.session_id = s.id
               WHERE s.user_id = ? AND m.content LIKE ?
               ORDER BY m.created_at DESC
               LIMIT 100""",
            (user_id, f"%{keyword}%"),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # ── Preset CRUD ────────────────────────────────────────

    async def create_preset(self, preset: Preset) -> Preset:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "INSERT INTO presets (user_id, name, description, system_prompt, is_builtin) VALUES (?, ?, ?, ?, ?)",
            (preset.user_id, preset.name, preset.description, preset.system_prompt, int(preset.is_builtin)),
        )
        await conn.commit()
        preset.id = cursor.lastrowid
        return preset

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        conn = self._ensure_conn()
        cursor = await conn.execute("SELECT * FROM presets WHERE id = ?", (preset_id,))
        row = await cursor.fetchone()
        return self._row_to_preset(row) if row else None

    async def list_presets(self, user_id: Optional[int] = None) -> list[Preset]:
        conn = self._ensure_conn()
        if user_id is None:
            cursor = await conn.execute(
                "SELECT * FROM presets WHERE is_builtin=1 OR user_id IS NOT NULL ORDER BY is_builtin DESC, id"
            )
        else:
            cursor = await conn.execute(
                "SELECT * FROM presets WHERE is_builtin=1 OR user_id=? ORDER BY is_builtin DESC, id",
                (user_id,),
            )
        rows = await cursor.fetchall()
        return [self._row_to_preset(r) for r in rows]

    async def update_preset(self, preset: Preset) -> Preset:
        conn = self._ensure_conn()
        await conn.execute(
            """UPDATE presets SET name=?, description=?, system_prompt=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=? AND is_builtin=0""",
            (preset.name, preset.description, preset.system_prompt, preset.id),
        )
        await conn.commit()
        return preset

    async def delete_preset(self, preset_id: int) -> bool:
        conn = self._ensure_conn()
        cursor = await conn.execute("DELETE FROM presets WHERE id = ? AND is_builtin = 0", (preset_id,))
        await conn.commit()
        return cursor.rowcount > 0

    # ── UserConfig CRUD ────────────────────────────────────

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        conn = self._ensure_conn()
        await conn.execute(
            """INSERT INTO user_configs (user_id, key, value, updated_at)
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id, key) DO UPDATE SET value=?, updated_at=CURRENT_TIMESTAMP""",
            (config.user_id, config.key, config.value, config.value),
        )
        await conn.commit()
        return config

    async def get_user_config(self, user_id: int, key: str) -> Optional[str]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT value FROM user_configs WHERE user_id=? AND key=?", (user_id, key)
        )
        row = await cursor.fetchone()
        return row["value"] if row else None

    async def list_user_configs(self, user_id: int) -> list[UserConfig]:
        conn = self._ensure_conn()
        cursor = await conn.execute(
            "SELECT * FROM user_configs WHERE user_id=? ORDER BY key", (user_id,)
        )
        rows = await cursor.fetchall()
        return [self._row_to_user_config(r) for r in rows]

    # ── Row 转换辅助方法 ──────────────────────────────────

    def _row_to_user(self, row: aiosqlite.Row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            default_model=row["default_model"],
            default_preset_id=row["default_preset_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_session(self, row: aiosqlite.Row) -> Session:
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            model_name=row["model_name"],
            preset_id=row["preset_id"],
            total_prompt_tokens=row["total_prompt_tokens"],
            total_completion_tokens=row["total_completion_tokens"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_message(self, row: aiosqlite.Row) -> Message:
        return Message(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            prompt_tokens=row["prompt_tokens"],
            completion_tokens=row["completion_tokens"],
            created_at=row["created_at"],
        )

    def _row_to_preset(self, row: aiosqlite.Row) -> Preset:
        return Preset(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            description=row["description"],
            system_prompt=row["system_prompt"],
            is_builtin=bool(row["is_builtin"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _row_to_user_config(self, row: aiosqlite.Row) -> UserConfig:
        return UserConfig(
            id=row["id"],
            user_id=row["user_id"],
            key=row["key"],
            value=row["value"],
            updated_at=row["updated_at"],
        )
