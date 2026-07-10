"""用户管理器单元测试"""

import pytest

from src.core.user_manager import UserManager


class TestUserManager:
    """UserManager 业务逻辑测试"""

    async def test_create_user(self, db):
        manager = UserManager(db)
        user = await manager.create_user("testuser1")
        assert user.id is not None
        assert user.username == "testuser1"

    async def test_create_duplicate_user(self, db):
        manager = UserManager(db)
        await manager.create_user("testuser2")
        with pytest.raises(ValueError, match="已存在"):
            await manager.create_user("testuser2")

    async def test_switch_user(self, db):
        manager = UserManager(db)
        await manager.create_user("testuser3")
        user = await manager.switch_user("testuser3")
        assert manager.current_user is not None
        assert manager.current_user.username == "testuser3"

    async def test_switch_nonexistent_user(self, db):
        manager = UserManager(db)
        with pytest.raises(ValueError, match="不存在"):
            await manager.switch_user("nobody")

    async def test_delete_user(self, db):
        manager = UserManager(db)
        await manager.create_user("testuser4")
        result = await manager.delete_user("testuser4")
        assert result is True

        # 确认已删除
        user = await manager.get_user_by_username("testuser4")
        assert user is None

    async def test_delete_current_user_clears_state(self, db):
        manager = UserManager(db)
        user = await manager.create_user("testuser5")
        manager._current_user = user
        await manager.delete_user("testuser5")
        assert manager.current_user is None

    async def test_list_users(self, db):
        manager = UserManager(db)
        await manager.create_user("user_a")
        await manager.create_user("user_b")
        users = await manager.list_users()
        assert len(users) == 2
