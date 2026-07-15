"""数据库初始化脚本 —— 建表 + 冒烟测试（CRUD 全链路验证）"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager
from src.models.schemas import Message, Preset, Session, User
from src.storage.factory import StorageFactory


async def smoke_test(backend) -> None:
    """冒烟测试：验证 CRUD 全链路"""
    print("  运行冒烟测试...")

    # 0. 清理上次可能残留的测试数据
    existing = await backend.get_user_by_username("_smoke_test_user")
    if existing:
        await backend.delete_user(existing.id)

    # 1. 创建用户
    user = User(username="_smoke_test_user", default_model="gpt-4o-mini")
    user = await backend.create_user(user)
    assert user.id is not None, "创建用户失败"
    print(f"[OK]创建用户 (id={user.id})")

    # 2. 创建会话
    session = Session(user_id=user.id, title="冒烟测试会话", model_name="gpt-4o-mini")
    session = await backend.create_session(session)
    assert session.id is not None, "创建会话失败"
    print(f"[OK]创建会话 (id={session.id})")

    # 3. 添加消息
    msg1 = Message(session_id=session.id, role="human", content="你好")
    msg1 = await backend.create_message(msg1)
    assert msg1.id is not None, "创建消息失败"

    msg2 = Message(session_id=session.id, role="ai", content="你好！有什么可以帮助你的？")
    msg2 = await backend.create_message(msg2)
    assert msg2.id is not None, "创建消息失败"
    print(f"[OK]添加消息 ({msg1.id}, {msg2.id})")

    # 4. 查询消息
    messages = await backend.list_messages_by_session(session.id)
    assert len(messages) == 2, f"消息查询失败: 期望2条, 实际{len(messages)}条"
    print(f"[OK]查询消息 ({len(messages)}条)")

    # 5. 搜索消息
    results = await backend.search_messages(user.id, "你好")
    assert len(results) >= 1, "消息搜索失败"
    print(f"[OK]搜索消息 ({len(results)}条匹配)")

    # 6. 列出会话
    sessions = await backend.list_sessions_by_user(user.id)
    assert len(sessions) == 1, f"会话列表失败: 期望1个, 实际{len(sessions)}个"
    print(f"[OK]列出会话 ({len(sessions)}个)")

    # 7. 创建预设
    preset = Preset(name="_smoke_test_preset", description="test", system_prompt="test", is_builtin=False)
    preset = await backend.create_preset(preset)
    assert preset.id is not None, "创建预设失败"
    print(f"[OK]创建预设 (id={preset.id})")

    # 8. 清理冒烟测试数据（级联删除用户→会话→消息）
    await backend.delete_user(user.id)
    deleted_user = await backend.get_user_by_id(user.id)
    assert deleted_user is None, "清理用户失败"
    print(f"[OK]清理测试数据")

    print("  冒烟测试全部通过!")


async def main() -> None:
    print("正在初始化数据库...")

    config = ConfigManager()
    storage_type = config.storage_type
    storage_config = config.storage_config

    print(f"  存储类型: {storage_type}")
    print(f"  运行环境: {config.app_env}")

    backend = StorageFactory.create(
        storage_type,
        sqlite_path=storage_config.get("sqlite", {}).get("path", "data/sqlite/app.db"),
    )

    await backend.initialize()
    print("  数据表创建完成!")

    await smoke_test(backend)

    await backend.close()
    print("数据库初始化成功!")


if __name__ == "__main__":
    asyncio.run(main())
