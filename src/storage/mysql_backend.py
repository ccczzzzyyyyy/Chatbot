"""MySQL 存储后端 —— 使用 aiomysql 实现异步 CRUD"""

from typing import Optional

import aiomysql

from src.models.schemas import Message, Preset, Session, User, UserConfig
from src.storage.base import StorageBackend


class MySQLBackend(StorageBackend):
    """MySQL 异步存储后端"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "langchain_chat",
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database
        self._pool: Optional[aiomysql.Pool] = None

    async def initialize(self) -> None:
        """初始化数据库连接池并创建表"""
        # 先连接不指定数据库，创建数据库
        conn = await aiomysql.connect(
            host=self._host, port=self._port,
            user=self._user, password=self._password,
            autocommit=True,
        )
        async with conn.cursor() as cur:
            await cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self._database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()

        # 创建连接池
        self._pool = await aiomysql.create_pool(
            host=self._host, port=self._port,
            user=self._user, password=self._password,
            db=self._database,
            autocommit=True,
            minsize=1, maxsize=10,
        )

        # 建表
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        default_model VARCHAR(50) DEFAULT 'gpt-4o-mini',
                        default_preset_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        title VARCHAR(200) DEFAULT '新对话',
                        model_name VARCHAR(50) DEFAULT 'gpt-4o-mini',
                        preset_id INT,
                        total_prompt_tokens INT DEFAULT 0,
                        total_completion_tokens INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_sessions_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        session_id INT NOT NULL,
                        role VARCHAR(20) NOT NULL,
                        content TEXT NOT NULL,
                        prompt_tokens INT DEFAULT 0,
                        completion_tokens INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                        INDEX idx_messages_session_id (session_id),
                        FULLTEXT INDEX idx_messages_content (content)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS presets (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT,
                        name VARCHAR(100) NOT NULL,
                        description TEXT DEFAULT '',
                        system_prompt TEXT DEFAULT '',
                        is_builtin TINYINT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_presets_user_id (user_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_configs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        `key` VARCHAR(100) NOT NULL,
                        `value` TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE KEY uk_user_key (user_id, `key`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)

    async def close(self) -> None:
        """关闭连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None

    async def _execute(self, sql: str, params: tuple = ()) -> aiomysql.Cursor:
        """执行 SQL 并返回 cursor"""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params)
                return cur

    async def _fetchone(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """执行查询并返回一行"""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params)
                return await cur.fetchone()

    async def _fetchall(self, sql: str, params: tuple = ()) -> list[dict]:
        """执行查询并返回所有行"""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params)
                return await cur.fetchall()

    async def _insert(self, sql: str, params: tuple = ()) -> int:
        """执行插入并返回 lastrowid"""
        async with self._pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, params)
                return cur.lastrowid

    async def _update(self, sql: str, params: tuple = ()) -> int:
        """执行更新并返回影响行数"""
        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                affected = await cur.execute(sql, params)
                return affected

    # ── User CRUD ──────────────────────────────────────────

    async def create_user(self, user: User) -> User:
        user_id = await self._insert(
            "INSERT INTO users (username, default_model, default_preset_id) VALUES (%s, %s, %s)",
            (user.username, user.default_model, user.default_preset_id),
        )
        user.id = user_id
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        row = await self._fetchone("SELECT * FROM users WHERE id = %s", (user_id,))
        return self._row_to_user(row) if row else None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        row = await self._fetchone("SELECT * FROM users WHERE username = %s", (username,))
        return self._row_to_user(row) if row else None

    async def list_users(self) -> list[User]:
        rows = await self._fetchall("SELECT * FROM users ORDER BY id")
        return [self._row_to_user(r) for r in rows]

    async def update_user(self, user: User) -> User:
        await self._update(
            "UPDATE users SET username=%s, default_model=%s, default_preset_id=%s WHERE id=%s",
            (user.username, user.default_model, user.default_preset_id, user.id),
        )
        return user

    async def delete_user(self, user_id: int) -> bool:
        affected = await self._update("DELETE FROM users WHERE id = %s", (user_id,))
        return affected > 0

    # ── Session CRUD ───────────────────────────────────────

    async def create_session(self, session: Session) -> Session:
        sid = await self._insert(
            "INSERT INTO sessions (user_id, title, model_name, preset_id) VALUES (%s, %s, %s, %s)",
            (session.user_id, session.title, session.model_name, session.preset_id),
        )
        session.id = sid
        return session

    async def get_session_by_id(self, session_id: int) -> Optional[Session]:
        row = await self._fetchone("SELECT * FROM sessions WHERE id = %s", (session_id,))
        return self._row_to_session(row) if row else None

    async def list_sessions_by_user(self, user_id: int) -> list[Session]:
        rows = await self._fetchall(
            "SELECT * FROM sessions WHERE user_id = %s ORDER BY updated_at DESC", (user_id,)
        )
        return [self._row_to_session(r) for r in rows]

    async def update_session(self, session: Session) -> Session:
        await self._update(
            """UPDATE sessions SET title=%s, model_name=%s, preset_id=%s,
               total_prompt_tokens=%s, total_completion_tokens=%s WHERE id=%s""",
            (session.title, session.model_name, session.preset_id,
             session.total_prompt_tokens, session.total_completion_tokens, session.id),
        )
        return session

    async def delete_session(self, session_id: int) -> bool:
        affected = await self._update("DELETE FROM sessions WHERE id = %s", (session_id,))
        return affected > 0

    # ── Message CRUD ───────────────────────────────────────

    async def create_message(self, message: Message) -> Message:
        mid = await self._insert(
            "INSERT INTO messages (session_id, role, content, prompt_tokens, completion_tokens) VALUES (%s, %s, %s, %s, %s)",
            (message.session_id, message.role, message.content, message.prompt_tokens, message.completion_tokens),
        )
        message.id = mid
        return message

    async def list_messages_by_session(self, session_id: int) -> list[Message]:
        rows = await self._fetchall(
            "SELECT * FROM messages WHERE session_id = %s ORDER BY created_at ASC", (session_id,)
        )
        return [self._row_to_message(r) for r in rows]

    async def search_messages(self, user_id: int, keyword: str) -> list[dict]:
        rows = await self._fetchall(
            """SELECT m.*, s.title as session_title
               FROM messages m
               JOIN sessions s ON m.session_id = s.id
               WHERE s.user_id = %s AND m.content LIKE %s
               ORDER BY m.created_at DESC
               LIMIT 100""",
            (user_id, f"%{keyword}%"),
        )
        return rows

    # ── Preset CRUD ────────────────────────────────────────

    async def create_preset(self, preset: Preset) -> Preset:
        pid = await self._insert(
            "INSERT INTO presets (user_id, name, description, system_prompt, is_builtin) VALUES (%s, %s, %s, %s, %s)",
            (preset.user_id, preset.name, preset.description, preset.system_prompt, int(preset.is_builtin)),
        )
        preset.id = pid
        return preset

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        row = await self._fetchone("SELECT * FROM presets WHERE id = %s", (preset_id,))
        return self._row_to_preset(row) if row else None

    async def list_presets(self, user_id: Optional[int] = None) -> list[Preset]:
        if user_id is None:
            rows = await self._fetchall(
                "SELECT * FROM presets WHERE is_builtin=1 OR user_id IS NOT NULL ORDER BY is_builtin DESC, id"
            )
        else:
            rows = await self._fetchall(
                "SELECT * FROM presets WHERE is_builtin=1 OR user_id=%s ORDER BY is_builtin DESC, id",
                (user_id,),
            )
        return [self._row_to_preset(r) for r in rows]

    async def update_preset(self, preset: Preset) -> Preset:
        await self._update(
            "UPDATE presets SET name=%s, description=%s, system_prompt=%s WHERE id=%s AND is_builtin=0",
            (preset.name, preset.description, preset.system_prompt, preset.id),
        )
        return preset

    async def delete_preset(self, preset_id: int) -> bool:
        affected = await self._update("DELETE FROM presets WHERE id = %s AND is_builtin = 0", (preset_id,))
        return affected > 0

    # ── UserConfig CRUD ────────────────────────────────────

    async def set_user_config(self, config: UserConfig) -> UserConfig:
        await self._update(
            """INSERT INTO user_configs (user_id, `key`, `value`)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE `value`=%s""",
            (config.user_id, config.key, config.value, config.value),
        )
        return config

    async def get_user_config(self, user_id: int, key: str) -> Optional[str]:
        row = await self._fetchone(
            "SELECT `value` FROM user_configs WHERE user_id=%s AND `key`=%s", (user_id, key)
        )
        return row["value"] if row else None

    async def list_user_configs(self, user_id: int) -> list[UserConfig]:
        rows = await self._fetchall(
            "SELECT * FROM user_configs WHERE user_id=%s ORDER BY `key`", (user_id,)
        )
        return [self._row_to_user_config(r) for r in rows]

    # ── Row 转换辅助方法 ──────────────────────────────────

    def _row_to_user(self, row: dict) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            default_model=row.get("default_model", "gpt-4o-mini"),
            default_preset_id=row.get("default_preset_id"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_session(self, row: dict) -> Session:
        return Session(
            id=row["id"],
            user_id=row["user_id"],
            title=row.get("title", "新对话"),
            model_name=row.get("model_name", "gpt-4o-mini"),
            preset_id=row.get("preset_id"),
            total_prompt_tokens=row.get("total_prompt_tokens", 0),
            total_completion_tokens=row.get("total_completion_tokens", 0),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_message(self, row: dict) -> Message:
        return Message(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            prompt_tokens=row.get("prompt_tokens", 0),
            completion_tokens=row.get("completion_tokens", 0),
            created_at=row.get("created_at"),
        )

    def _row_to_preset(self, row: dict) -> Preset:
        return Preset(
            id=row["id"],
            user_id=row.get("user_id"),
            name=row["name"],
            description=row.get("description", ""),
            system_prompt=row.get("system_prompt", ""),
            is_builtin=bool(row.get("is_builtin", 0)),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_user_config(self, row: dict) -> UserConfig:
        return UserConfig(
            id=row["id"],
            user_id=row["user_id"],
            key=row["key"],
            value=row["value"],
            updated_at=row.get("updated_at"),
        )
