"""pytest fixtures —— 共享测试资源"""

import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# 确保 src 目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.sqlite_backend import SQLiteBackend

TEST_DB_PATH = "data/sqlite/test_app.db"


@pytest_asyncio.fixture
async def db():
    """创建测试数据库实例"""
    # 清理旧测试数据
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    backend = SQLiteBackend(db_path=TEST_DB_PATH)
    await backend.initialize()
    yield backend
    await backend.close()

    # 清理
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_with_user(db):
    """创建含有一个用户的数据库"""
    from src.models.schemas import User

    user = User(username="testuser", default_model="gpt-4o-mini")
    user = await db.create_user(user)
    return db, user


@pytest_asyncio.fixture
async def db_with_session(db_with_user):
    """创建含有一个用户和一个会话的数据库"""
    from src.models.schemas import Session

    db, user = db_with_user
    session = Session(user_id=user.id, title="测试会话", model_name="gpt-4o-mini")
    session = await db.create_session(session)
    return db, user, session
