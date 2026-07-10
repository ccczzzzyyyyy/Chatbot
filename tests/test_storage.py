"""存储层单元测试 —— SQLite 后端 CRUD"""

import pytest

from src.models.schemas import Message, Preset, Session, User, UserConfig


class TestUserCRUD:
    """用户 CRUD 测试"""

    async def test_create_user(self, db):
        user = User(username="alice", default_model="gpt-4o")
        created = await db.create_user(user)
        assert created.id is not None
        assert created.username == "alice"

    async def test_create_duplicate_user(self, db):
        await db.create_user(User(username="bob"))
        with pytest.raises(Exception):
            await db.create_user(User(username="bob"))

    async def test_get_user_by_id(self, db):
        user = await db.create_user(User(username="charlie"))
        fetched = await db.get_user_by_id(user.id)
        assert fetched is not None
        assert fetched.username == "charlie"

    async def test_get_user_by_username(self, db):
        await db.create_user(User(username="dave"))
        fetched = await db.get_user_by_username("dave")
        assert fetched is not None
        assert fetched.username == "dave"

    async def test_get_nonexistent_user(self, db):
        fetched = await db.get_user_by_id(99999)
        assert fetched is None
        fetched = await db.get_user_by_username("nonexistent")
        assert fetched is None

    async def test_list_users(self, db):
        await db.create_user(User(username="user1"))
        await db.create_user(User(username="user2"))
        users = await db.list_users()
        assert len(users) == 2

    async def test_update_user(self, db):
        user = await db.create_user(User(username="eve"))
        user.default_model = "gpt-4o"
        updated = await db.update_user(user)
        assert updated.default_model == "gpt-4o"

        fetched = await db.get_user_by_id(user.id)
        assert fetched.default_model == "gpt-4o"

    async def test_delete_user(self, db):
        user = await db.create_user(User(username="frank"))
        result = await db.delete_user(user.id)
        assert result is True

        fetched = await db.get_user_by_id(user.id)
        assert fetched is None

    async def test_delete_nonexistent_user(self, db):
        result = await db.delete_user(99999)
        assert result is False


class TestSessionCRUD:
    """会话 CRUD 测试"""

    async def test_create_session(self, db_with_user):
        db, user = db_with_user
        session = Session(user_id=user.id, title="测试", model_name="gpt-4o")
        created = await db.create_session(session)
        assert created.id is not None
        assert created.title == "测试"

    async def test_get_session_by_id(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id, title="会话1"))
        fetched = await db.get_session_by_id(session.id)
        assert fetched is not None
        assert fetched.title == "会话1"

    async def test_list_sessions_by_user(self, db_with_user):
        db, user = db_with_user
        await db.create_session(Session(user_id=user.id, title="A"))
        await db.create_session(Session(user_id=user.id, title="B"))
        sessions = await db.list_sessions_by_user(user.id)
        assert len(sessions) == 2

    async def test_update_session(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id, title="原始"))
        session.title = "已修改"
        await db.update_session(session)
        fetched = await db.get_session_by_id(session.id)
        assert fetched.title == "已修改"

    async def test_delete_session(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id))
        result = await db.delete_session(session.id)
        assert result is True
        fetched = await db.get_session_by_id(session.id)
        assert fetched is None


class TestMessageCRUD:
    """消息 CRUD 测试"""

    async def test_create_message(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id))
        msg = Message(session_id=session.id, role="human", content="你好")
        created = await db.create_message(msg)
        assert created.id is not None
        assert created.content == "你好"

    async def test_list_messages(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id))
        await db.create_message(Message(session_id=session.id, role="human", content="Q1"))
        await db.create_message(Message(session_id=session.id, role="ai", content="A1"))
        messages = await db.list_messages_by_session(session.id)
        assert len(messages) == 2

    async def test_search_messages(self, db_with_user):
        db, user = db_with_user
        session = await db.create_session(Session(user_id=user.id, title="搜索测试"))
        await db.create_message(Message(session_id=session.id, role="human", content="Python 怎么学"))
        await db.create_message(Message(session_id=session.id, role="ai", content="可以从基础语法开始"))

        results = await db.search_messages(user.id, "Python")
        assert len(results) == 1
        assert results[0]["session_title"] == "搜索测试"

        results = await db.search_messages(user.id, "不存在的关键词")
        assert len(results) == 0


class TestPresetCRUD:
    """预设 CRUD 测试"""

    async def test_create_preset(self, db):
        preset = Preset(name="测试预设", system_prompt="你是一个测试助手", is_builtin=True)
        created = await db.create_preset(preset)
        assert created.id is not None
        assert created.name == "测试预设"

    async def test_list_presets(self, db):
        await db.create_preset(Preset(name="内置1", is_builtin=True))
        await db.create_preset(Preset(name="自定义1", user_id=1, is_builtin=False))
        presets = await db.list_presets(user_id=1)
        assert len(presets) == 2

    async def test_update_preset(self, db):
        preset = await db.create_preset(Preset(name="原名称", system_prompt=""))
        preset.name = "新名称"
        await db.update_preset(preset)
        fetched = await db.get_preset_by_id(preset.id)
        assert fetched.name == "新名称"

    async def test_delete_preset(self, db):
        preset = await db.create_preset(Preset(name="待删除", is_builtin=False))
        result = await db.delete_preset(preset.id)
        assert result is True

    async def test_cannot_delete_builtin(self, db):
        preset = await db.create_preset(Preset(name="系统预设", is_builtin=True))
        result = await db.delete_preset(preset.id)
        assert result is False


class TestUserConfigCRUD:
    """用户配置 CRUD 测试"""

    async def test_set_config(self, db):
        config = UserConfig(user_id=1, key="theme", value="dark")
        await db.set_user_config(config)
        value = await db.get_user_config(1, "theme")
        assert value == "dark"

    async def test_update_config(self, db):
        await db.set_user_config(UserConfig(user_id=1, key="lang", value="zh"))
        await db.set_user_config(UserConfig(user_id=1, key="lang", value="en"))
        value = await db.get_user_config(1, "lang")
        assert value == "en"

    async def test_get_nonexistent_config(self, db):
        value = await db.get_user_config(1, "nonexistent")
        assert value is None
