"""TUI 主应用 —— 菜单路由、状态管理"""

from src.interface.ui_protocol import AbstractUI
from src.ui.tui.chat_view import ChatView
from src.ui.tui.menu_view import MenuView


class TUIApp(AbstractUI):
    """TUI 主应用程序，管理菜单路由和应用状态"""

    def __init__(self) -> None:
        self.menu = MenuView()
        self.chat = ChatView()
        self._running = False
        self._current_user: dict | None = None
        self._current_session: dict | None = None

    @property
    def current_user(self) -> dict | None:
        return self._current_user

    @property
    def current_session(self) -> dict | None:
        return self._current_session

    async def run(self) -> None:
        """启动 TUI 主循环"""
        self._running = True
        while self._running:
            action = await self.menu.show_main_menu()
            await self._handle_action(action)

    async def _handle_action(self, action: str) -> None:
        """根据主菜单选择路由到对应功能"""
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

    # ── 各菜单处理（当前为桩实现，后续步骤逐步填充） ──────

    async def _handle_chat(self) -> None:
        """开始对话"""
        if not self._current_user:
            self.menu.show_message("请先创建或选择用户", "warning")
            return
        self.menu.show_message("对话功能将在 Step 7 实现", "info")

    async def _handle_user_menu(self) -> None:
        """用户管理菜单"""
        while True:
            action = await self.menu.show_user_menu()
            if action == "back":
                break
            self.menu.show_message("用户管理功能将在 Step 4 实现", "info")

    async def _handle_session_menu(self) -> None:
        """会话管理菜单"""
        while True:
            action = await self.menu.show_session_menu()
            if action == "back":
                break
            self.menu.show_message("会话管理功能将在 Step 7-8 实现", "info")

    async def _handle_preset_menu(self) -> None:
        """预设管理菜单"""
        while True:
            action = await self.menu.show_preset_menu()
            if action == "back":
                break
            self.menu.show_message("预设管理功能将在 Step 5 实现", "info")

    async def _handle_search(self) -> None:
        """对话搜索"""
        self.menu.show_message("搜索功能将在 Step 9 实现", "info")

    async def _handle_export(self) -> None:
        """导出对话"""
        self.menu.show_message("导出功能将在 Step 10 实现", "info")

    async def _handle_model_settings(self) -> None:
        """模型设置"""
        self.menu.show_message("模型设置功能将在 Step 10 实现", "info")

    async def _handle_settings(self) -> None:
        """系统设置"""
        self.menu.show_message("系统设置功能将在后续步骤实现", "info")

    async def _handle_quit(self) -> None:
        """退出程序"""
        self._running = False
        self.menu.show_message("再见！", "success")

    # ── UI 协议接口方法 ──────────────────────────────────

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
