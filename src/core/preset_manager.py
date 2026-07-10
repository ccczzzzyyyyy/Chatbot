"""预设管理器 —— 内置预设 + 用户自定义预设的 CRUD"""

import os
from typing import Optional

import yaml

from src.models.schemas import Preset
from src.storage.base import StorageBackend


class PresetManager:
    """预设 Prompt 管理业务逻辑"""

    def __init__(self, storage: StorageBackend, user_id: Optional[int] = None) -> None:
        self._storage = storage
        self._user_id = user_id

    @property
    def user_id(self) -> Optional[int]:
        return self._user_id

    @user_id.setter
    def user_id(self, value: Optional[int]) -> None:
        self._user_id = value

    async def load_builtin_presets(self) -> list[Preset]:
        """从 presets.yaml 加载系统内置预设到数据库（如尚未加载）"""
        existing = await self._storage.list_presets(user_id=None)
        if any(p.is_builtin for p in existing):
            return [p for p in existing if p.is_builtin]

        presets_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "config", "presets.yaml"
        )
        presets_path = os.path.normpath(presets_path)
        if not os.path.exists(presets_path):
            return []

        with open(presets_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        builtins = []
        for p_data in data.get("presets", []):
            preset = Preset(
                name=p_data["name"],
                description=p_data.get("description", ""),
                system_prompt=p_data.get("system_prompt", ""),
                is_builtin=True,
            )
            preset = await self._storage.create_preset(preset)
            builtins.append(preset)

        return builtins

    async def list_all_presets(self) -> list[Preset]:
        """列出所有预设（内置 + 当前用户自定义）"""
        await self.load_builtin_presets()
        return await self._storage.list_presets(user_id=self._user_id)

    async def list_user_presets(self) -> list[Preset]:
        """列出当前用户的自定义预设"""
        if self._user_id is None:
            return []
        all_presets = await self._storage.list_presets(user_id=self._user_id)
        return [p for p in all_presets if not p.is_builtin]

    async def create_preset(self, name: str, description: str, system_prompt: str) -> Preset:
        """创建用户自定义预设"""
        if self._user_id is None:
            raise ValueError("请先登录用户")

        preset = Preset(
            user_id=self._user_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            is_builtin=False,
        )
        return await self._storage.create_preset(preset)

    async def update_preset(self, preset_id: int, name: str, description: str, system_prompt: str) -> Preset:
        """更新用户自定义预设"""
        existing = await self._storage.get_preset_by_id(preset_id)
        if not existing:
            raise ValueError("预设不存在")
        if existing.is_builtin:
            raise ValueError("系统内置预设不可修改")
        if existing.user_id != self._user_id:
            raise ValueError("只能修改自己的预设")

        existing.name = name
        existing.description = description
        existing.system_prompt = system_prompt
        return await self._storage.update_preset(existing)

    async def delete_preset(self, preset_id: int) -> bool:
        """删除用户自定义预设"""
        existing = await self._storage.get_preset_by_id(preset_id)
        if not existing:
            raise ValueError("预设不存在")
        if existing.is_builtin:
            raise ValueError("系统内置预设不可删除")
        if existing.user_id != self._user_id:
            raise ValueError("只能删除自己的预设")

        return await self._storage.delete_preset(preset_id)

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        """根据 ID 获取预设"""
        return await self._storage.get_preset_by_id(preset_id)
