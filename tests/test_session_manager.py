"""会话管理器单元测试"""

import pytest

from src.core.session_manager import SessionManager


class TestSessionManager:
    """SessionManager 业务逻辑测试"""

    async def test_create_session(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1, model_name="gpt-4o")
        assert session.id is not None
        assert session.title == "新对话"
        assert manager.current_session is not None

    async def test_create_session_with_title(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1, title="自定义标题")
        assert session.title == "自定义标题"

    async def test_save_message(self, db):
        manager = SessionManager(db)
        await manager.create_session(user_id=1)

        msg = await manager.save_message(role="human", content="你好")
        assert msg.id is not None
        assert msg.role == "human"

    async def test_save_message_auto_title(self, db):
        manager = SessionManager(db)
        await manager.create_session(user_id=1)
        await manager.save_message(role="human", content="这是一条很长的消息用来测试自动标题生成功能")
        assert manager.current_session.title != "新对话"
        assert len(manager.current_session.title) <= 30

    async def test_get_session_messages(self, db):
        manager = SessionManager(db)
        await manager.create_session(user_id=1)
        await manager.save_message(role="human", content="Q1")
        await manager.save_message(role="ai", content="A1")

        messages = await manager.get_session_messages(manager.current_session.id)
        assert len(messages) == 2

    async def test_list_user_sessions(self, db):
        manager = SessionManager(db)
        await manager.create_session(user_id=1, title="会话A")
        await manager.create_session(user_id=1, title="会话B")

        sessions = await manager.list_user_sessions(1)
        assert len(sessions) == 2

    async def test_rename_session(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1, title="原标题")
        renamed = await manager.rename_session(session.id, "新标题")
        assert renamed.title == "新标题"

    async def test_delete_session(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1)
        result = await manager.delete_session(session.id)
        assert result is True

    async def test_delete_current_session(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1)
        assert manager.current_session is not None
        await manager.delete_session(session.id)
        assert manager.current_session is None

    async def test_load_nonexistent_session(self, db):
        manager = SessionManager(db)
        with pytest.raises(ValueError, match="不存在"):
            await manager.load_session(99999)

    async def test_search_messages(self, db):
        manager = SessionManager(db)
        session = await manager.create_session(user_id=1, title="搜索测试")
        await manager.save_message(role="human", content="Python 编程")
        await manager.save_message(role="ai", content="Python 是一门流行的语言")

        results = await manager.search_messages(1, "Python")
        assert len(results) == 2
