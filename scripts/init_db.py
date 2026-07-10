"""数据库初始化脚本 —— 创建所有数据表"""

import asyncio
import sys
from pathlib import Path

# 将项目根目录加入 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config_manager import ConfigManager
from src.storage.factory import StorageFactory


async def main() -> None:
    print("正在初始化数据库...")

    config = ConfigManager()
    storage_type = config.storage_type
    storage_config = config.storage_config

    print(f"  存储类型: {storage_type}")

    backend = StorageFactory.create(
        storage_type,
        sqlite_path=storage_config.get("sqlite", {}).get("path", "data/sqlite/app.db"),
    )

    await backend.initialize()
    print("  数据表创建完成!")

    await backend.close()
    print("数据库初始化成功!")


if __name__ == "__main__":
    asyncio.run(main())
