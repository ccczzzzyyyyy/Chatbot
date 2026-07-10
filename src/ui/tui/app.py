"""TUI 主应用 —— 菜单路由、状态管理"""

import asyncio
from datetime import datetime

from src.core.config_manager import ConfigManager
from src.core.user_manager import UserManager
from src.interface.ui_protocol import AbstractUI
from src.storage.factory import StorageFactory
from src.ui.tui.chat_view import ChatView
from src.ui.tui.menu_view import MenuView


class TUIApp(AbstractUI):
    """TUI 主应用程序，管理菜单路由和应用状态"""

    def __init__(self) -> None:
        self.menu = MenuView()
        self.chat = ChatView()
        self._running = False
        self._config: ConfigManager | None = None
        self._storage = None
        self._user_manager: UserManager | None = None

    @property
    def current_user(self) -> dict | None:
        if self._user_manager and self._user_manager.current_user:
            u = self._user_manager.current_user
            return {"id": u.id, "username": u.username, "default_model": u.default_model}
        return None

    async def run(self) -> None:
        """启动 TUI 主循环"""
        # 初始化配置和存储
        self._config = ConfigManager()
        storage_config = self._config.storage_config
        self._storage = StorageFactory.create(
            self._config.storage_type,
            sqlite_path=storage_config.get("sqlite", {}).get("path", "data/sqlite/app.db"),
        )
        await self._storage.initialize()
        self._user_manager = UserManager(self._storage)

        # 加载系统内置预设到数据库（如果尚未加载）
        await self._ensure_builtin_presets()

        self._running = True
        try:
            while self._running:
                action = await self.menu.show_main_menu()
                await self._handle_action(action)
        finally:
            await self._storage.close()

    async def _ensure_builtin_presets(self) -> None:
        """确保系统内置预设已加载到数据库"""
        import os

        import yaml

        from src.models.schemas import Preset

        existing = await self._storage.list_presets(user_id=None)
        if any(p.is_builtin for p in existing):
            return  # 已加载

        presets_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "presets.yaml")
        presets_path = os.path.normpath(presets_path)
        if not os.path.exists(presets_path):
            return

        with open(presets_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for p_data in data.get("presets", []):
            preset = Preset(
                name=p_data["name"],
                description=p_data.get("description", ""),
                system_prompt=p_data.get("system_prompt", ""),
                is_builtin=True,
            )
            await self._storage.create_preset(preset)

    # ── 路由处理 ──────────────────────────────────────────

    async def _handle_action(self, action: str) -> None:
        if action == "chat":
            await self._handle_chat()
        elif action == "user_menu":
            await self._handle_user_menu()
        elif action == "session_menu":
            await self._handle_session_menu()
        elif action == "preset_menu":
            await self._handle_preset_menu()
        elif action == "search":
            await self._handle_search()
        elif action == "export":
            await self._handle_export()
        elif action == "model_settings":
            await self._handle_model_settings()
        elif action == "settings":
            await self._handle_settings()
        elif action == "quit":
            await self._handle_quit()

    # ── 用户管理（Step 4 实现） ────────────────────────────

    async def _handle_user_menu(self) -> None:
        while True:
            action = await self.menu.show_user_menu()
            if action == "back":
                break
            elif action == "create_user":
                await self._do_create_user()
            elif action == "switch_user":
                await self._do_switch_user()
            elif action == "delete_user":
                await self._do_delete_user()
            elif action == "list_users":
                await self._do_list_users()

    async def _do_create_user(self) -> None:
        username = await self.menu.get_text_input("请输入用户名")
        if not username:
            return
        try:
            user = await self._user_manager.create_user(username)
            self._user_manager._current_user = user
            self.menu.show_message(f"用户 '{username}' 创建成功，已自动登录", "success")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_switch_user(self) -> None:
        username = await self.menu.get_text_input("请输入要切换的用户名")
        if not username:
            return
        try:
            user = await self._user_manager.switch_user(username)
            self.menu.show_message(f"已切换到用户 '{user.username}'", "success")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_delete_user(self) -> None:
        username = await self.menu.get_text_input("请输入要删除的用户名")
        if not username:
            return
        confirmed = await self.menu.get_confirmation(f"确定要删除用户 '{username}' 及其所有数据吗？此操作不可撤销")
        if not confirmed:
            self.menu.show_message("已取消删除", "info")
            return
        try:
            await self._user_manager.delete_user(username)
            self.menu.show_message(f"用户 '{username}' 已删除", "success")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_list_users(self) -> None:
        users = await self._user_manager.list_users()
        user_list = []
        for u in users:
            current_mark = " (当前)" if self._user_manager.current_user and self._user_manager.current_user.id == u.id else ""
            user_list.append({
                "id": str(u.id),
                "username": u.username + current_mark,
                "default_model": u.default_model,
                "created_at": str(u.created_at)[:19] if u.created_at else "",
            })
        self.menu.show_user_list(user_list)
        await self._wait_enter()

    # ── 其它功能（后续步骤实现） ──────────────────────────

    async def _handle_chat(self) -> None:
        if not self._user_manager or not self._user_manager.current_user:
            self.menu.show_message("请先创建或选择用户", "warning")
            return
        self.menu.show_message("对话功能将在 Step 7 实现", "info")

    async def _handle_session_menu(self) -> None:
        while True:
            action = await self.menu.show_session_menu()
            if action == "back":
                break
            self.menu.show_message("会话管理功能将在 Step 7-8 实现", "info")

    async def _handle_preset_menu(self) -> None:
        while True:
            action = await self.menu.show_preset_menu()
            if action == "back":
                break
            self.menu.show_message("预设管理功能将在 Step 5 实现", "info")

    async def _handle_search(self) -> None:
        self.menu.show_message("搜索功能将在 Step 9 实现", "info")

    async def _handle_export(self) -> None:
        self.menu.show_message("导出功能将在 Step 10 实现", "info")

    async def _handle_model_settings(self) -> None:
        self.menu.show_message("模型设置功能将在 Step 10 实现", "info")

    async def _handle_settings(self) -> None:
        self.menu.show_message("系统设置功能将在后续步骤实现", "info")

    async def _handle_quit(self) -> None:
        self._running = False
        self.menu.show_message("再见！", "success")

    async def _wait_enter(self) -> None:
        """等待用户按回车继续"""
        await self.menu.get_text_input("按回车键继续")

    # ── UI 协议接口方法（桩实现） ──────────────────────────

    async def display_message(self, content: str, role: str = "ai") -> None:
        pass

    async def display_stream(self, chunk: str) -> None:
        pass

    async def display_error(self, message: str) -> None:
        pass

    async def display_info(self, message: str) -> None:
        pass

    async def get_input(self, prompt_text: str = "> ") -> str:
        return ""

    async def get_confirmation(self, prompt_text: str) -> bool:
        return False

    async def show_menu(self, title: str, options: list[str]) -> int:
        return 0

    async def show_table(self, title: str, headers: list[str], rows: list[list[str]]) -> None:
        pass
