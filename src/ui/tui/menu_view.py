"""菜单视图 —— 用户/会话/预设/设置等菜单界面"""

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.shortcuts import clear as clear_screen

from src.ui.tui.widgets import (
    console,
    print_error,
    print_info,
    print_subtitle,
    print_success,
    print_title,
    print_warning,
    render_table,
)


class MenuView:
    """TUI 菜单视图，负责各类菜单的展示与交互"""

    def __init__(self) -> None:
        self._session = PromptSession(history=InMemoryHistory())

    # ── 主菜单 ────────────────────────────────────────────

    async def show_main_menu(self) -> str:
        """显示主菜单，返回用户选择的操作码"""
        clear_screen()
        print_title("LangChain Chat - 多轮会话系统")
        print_subtitle("主菜单")

        options = {
            "1": ("开始对话", "chat"),
            "2": ("用户管理", "user_menu"),
            "3": ("会话管理", "session_menu"),
            "4": ("预设管理", "preset_menu"),
            "5": ("对话搜索", "search"),
            "6": ("导出对话", "export"),
            "7": ("模型设置", "model_settings"),
            "8": ("系统设置", "settings"),
            "0": ("退出程序", "quit"),
        }

        for key, (label, _) in options.items():
            console.print(f"  [{key}] {label}")

        console.print()
        choice = await self._get_choice("请选择操作", list(options.keys()))
        return options[choice][1]

    # ── 用户菜单 ──────────────────────────────────────────

    async def show_user_menu(self) -> str:
        """显示用户管理菜单"""
        clear_screen()
        print_title("用户管理")

        options = {
            "1": ("创建用户", "create_user"),
            "2": ("切换用户", "switch_user"),
            "3": ("删除用户", "delete_user"),
            "4": ("用户列表", "list_users"),
            "0": ("返回主菜单", "back"),
        }

        for key, (label, _) in options.items():
            console.print(f"  [{key}] {label}")

        console.print()
        choice = await self._get_choice("请选择操作", list(options.keys()))
        return options[choice][1]

    # ── 会话菜单 ──────────────────────────────────────────

    async def show_session_menu(self) -> str:
        """显示会话管理菜单"""
        clear_screen()
        print_title("会话管理")

        options = {
            "1": ("新建会话", "new_session"),
            "2": ("加载历史会话", "load_session"),
            "3": ("会话列表", "list_sessions"),
            "4": ("重命名会话", "rename_session"),
            "5": ("删除会话", "delete_session"),
            "0": ("返回主菜单", "back"),
        }

        for key, (label, _) in options.items():
            console.print(f"  [{key}] {label}")

        console.print()
        choice = await self._get_choice("请选择操作", list(options.keys()))
        return options[choice][1]

    # ── 预设菜单 ──────────────────────────────────────────

    async def show_preset_menu(self) -> str:
        """显示预设管理菜单"""
        clear_screen()
        print_title("预设管理")

        options = {
            "1": ("预设列表", "list_presets"),
            "2": ("选择预设", "select_preset"),
            "3": ("新增预设", "create_preset"),
            "4": ("编辑预设", "edit_preset"),
            "5": ("删除预设", "delete_preset"),
            "0": ("返回主菜单", "back"),
        }

        for key, (label, _) in options.items():
            console.print(f"  [{key}] {label}")

        console.print()
        choice = await self._get_choice("请选择操作", list(options.keys()))
        return options[choice][1]

    # ── 用户输入辅助方法 ──────────────────────────────────

    async def get_text_input(self, prompt_text: str) -> str:
        """获取用户文本输入"""
        try:
            result = await self._session.prompt_async(f"{prompt_text}: ")
            return result.strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    async def get_confirmation(self, prompt_text: str) -> bool:
        """获取用户确认"""
        try:
            result = await self._session.prompt_async(f"{prompt_text} (y/n): ")
            return result.strip().lower() in ("y", "yes", "是")
        except (EOFError, KeyboardInterrupt):
            return False

    async def _get_choice(self, prompt_text: str, valid_choices: list[str]) -> str:
        """获取用户菜单选择"""
        while True:
            try:
                choice = await self._session.prompt_async(f"{prompt_text}: ")
                choice = choice.strip()
                if choice in valid_choices:
                    return choice
                print_error(f"无效选择，请输入: {', '.join(valid_choices)}")
            except (EOFError, KeyboardInterrupt):
                return "0"

    # ── 信息展示辅助方法 ──────────────────────────────────

    def show_user_list(self, users: list[dict]) -> None:
        """展示用户列表"""
        if not users:
            print_info("暂无用户")
            return
        rows = [[u["id"], u["username"], u.get("default_model", ""), u.get("created_at", "")] for u in users]
        render_table("用户列表", ["ID", "用户名", "默认模型", "创建时间"], rows)

    def show_session_list(self, sessions: list[dict]) -> None:
        """展示会话列表"""
        if not sessions:
            print_info("暂无会话")
            return
        rows = [
            [s["id"], s.get("title", ""), s.get("model_name", ""), s.get("created_at", ""), s.get("updated_at", "")]
            for s in sessions
        ]
        render_table("会话列表", ["ID", "标题", "模型", "创建时间", "更新时间"], rows)

    def show_preset_list(self, presets: list[dict]) -> None:
        """展示预设列表"""
        if not presets:
            print_info("暂无预设")
            return
        rows = [
            [
                p["id"],
                p.get("name", ""),
                p.get("description", ""),
                "系统内置" if p.get("is_builtin") else "自定义",
            ]
            for p in presets
        ]
        render_table("预设列表", ["ID", "名称", "描述", "类型"], rows)

    def show_message(self, text: str, style: str = "info") -> None:
        """根据风格显示消息"""
        if style == "success":
            print_success(text)
        elif style == "error":
            print_error(text)
        elif style == "warning":
            print_warning(text)
        else:
            print_info(text)
