"""会话管理器 —— 会话生命周期管理（创建/加载/保存/搜索/导出）"""

import os
from datetime import datetime
from typing import Optional

from src.models.schemas import Message, Session
from src.storage.base import StorageBackend


class SessionManager:
    """会话管理业务逻辑"""

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage
        self._current_session: Optional[Session] = None

    @property
    def current_session(self) -> Optional[Session]:
        return self._current_session

    async def create_session(
        self,
        user_id: int,
        model_name: str = "gpt-4o-mini",
        preset_id: Optional[int] = None,
        title: str = "新对话",
    ) -> Session:
        """创建新会话"""
        session = Session(
            user_id=user_id,
            title=title,
            model_name=model_name,
            preset_id=preset_id,
        )
        session = await self._storage.create_session(session)
        self._current_session = session
        return session

    async def load_session(self, session_id: int) -> Session:
        """加载已有会话"""
        session = await self._storage.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")
        self._current_session = session
        return session

    async def save_message(
        self,
        role: str,
        content: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> Message:
        """保存一条消息到当前会话"""
        if not self._current_session:
            raise RuntimeError("当前没有活跃会话")

        message = Message(
            session_id=self._current_session.id,
            role=role,
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        message = await self._storage.create_message(message)

        # 如果是用户首条消息且会话标题为"新对话"，自动生成标题
        if role == "human" and self._current_session.title == "新对话":
            title = content[:30].replace("\n", " ")
            await self.set_session_title(title)

        # 更新会话 token 计数
        if prompt_tokens or completion_tokens:
            self._current_session.total_prompt_tokens += prompt_tokens
            self._current_session.total_completion_tokens += completion_tokens
            await self._storage.update_session(self._current_session)

        return message

    async def get_session_messages(self, session_id: int) -> list[Message]:
        """获取会话的所有消息"""
        return await self._storage.list_messages_by_session(session_id)

    async def list_user_sessions(self, user_id: int) -> list[Session]:
        """列出用户的所有会话"""
        return await self._storage.list_sessions_by_user(user_id)

    async def set_session_title(self, title: str) -> Session:
        """设置会话标题"""
        if not self._current_session:
            raise RuntimeError("当前没有活跃会话")
        self._current_session.title = title
        self._current_session = await self._storage.update_session(self._current_session)
        return self._current_session

    async def rename_session(self, session_id: int, new_title: str) -> Session:
        """重命名会话"""
        session = await self._storage.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")
        session.title = new_title
        return await self._storage.update_session(session)

    async def delete_session(self, session_id: int) -> bool:
        """删除会话"""
        if self._current_session and self._current_session.id == session_id:
            self._current_session = None
        return await self._storage.delete_session(session_id)

    async def search_messages(self, user_id: int, keyword: str) -> list[dict]:
        """搜索消息"""
        return await self._storage.search_messages(user_id, keyword)

    async def export_session_to_markdown(self, session_id: int, export_dir: str = "data/users") -> str:
        """导出会话为 Markdown 文件，返回文件路径"""
        session = await self._storage.get_session_by_id(session_id)
        if not session:
            raise ValueError(f"会话 {session_id} 不存在")

        messages = await self._storage.list_messages_by_session(session_id)

        # 构建 Markdown 内容
        date_str = datetime.now().strftime("%Y-%m-%d")
        lines = [
            f"# {session.title}",
            "",
            f"- **日期**: {date_str}",
            f"- **模型**: {session.model_name}",
            f"- **Token 用量**: prompt={session.total_prompt_tokens}, completion={session.total_completion_tokens}",
            "",
            "---",
            "",
        ]

        for msg in messages:
            role_label = "**用户**" if msg.role == "human" else "**AI**"
            lines.append(f"### {role_label}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)

        # 创建导出目录
        safe_title = session.title.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filename = f"{safe_title}_{date_str}.md"
        filepath = os.path.join(export_dir, str(session.user_id), "exports")
        os.makedirs(filepath, exist_ok=True)
        full_path = os.path.join(filepath, filename)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

        return full_path
