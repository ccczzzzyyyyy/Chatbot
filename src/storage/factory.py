"""存储后端工厂 —— 根据配置创建对应的存储后端实例"""

from src.storage.base import StorageBackend
from src.storage.sqlite_backend import SQLiteBackend


class StorageFactory:
    """存储后端工厂，根据配置创建实例"""

    _backends = {
        "sqlite": SQLiteBackend,
    }

    @classmethod
    def register(cls, name: str, backend_cls: type) -> None:
        """注册新的存储后端"""
        cls._backends[name] = backend_cls

    @classmethod
    def create(cls, storage_type: str, **kwargs) -> StorageBackend:
        """根据类型创建存储后端实例"""
        backend_cls = cls._backends.get(storage_type)
        if backend_cls is None:
            raise ValueError(f"不支持的存储类型: {storage_type}，可用类型: {list(cls._backends.keys())}")

        if storage_type == "sqlite":
            db_path = kwargs.get("sqlite_path", "data/sqlite/app.db")
            return backend_cls(db_path=db_path)

        return backend_cls(**kwargs)
