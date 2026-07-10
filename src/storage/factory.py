"""存储后端工厂 —— 根据配置创建对应的存储后端实例"""

from src.storage.base import StorageBackend
from src.storage.file_backend import FileBackend
from src.storage.mysql_backend import MySQLBackend
from src.storage.sqlite_backend import SQLiteBackend


class StorageFactory:
    """存储后端工厂，根据配置创建实例"""

    _backends = {
        "sqlite": SQLiteBackend,
        "mysql": MySQLBackend,
        "file": FileBackend,
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

        if storage_type == "mysql":
            return backend_cls(
                host=kwargs.get("mysql_host", "localhost"),
                port=kwargs.get("mysql_port", 3306),
                user=kwargs.get("mysql_user", "root"),
                password=kwargs.get("mysql_password", ""),
                database=kwargs.get("mysql_database", "langchain_chat"),
            )

        if storage_type == "file":
            data_dir = kwargs.get("file_data_dir", "data/file_storage")
            return backend_cls(data_dir=data_dir)

        return backend_cls(**kwargs)
