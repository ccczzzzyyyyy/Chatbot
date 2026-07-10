"""TUI 主应用 —— 菜单路由、状态管理"""

import logging
import logging.config
import os

from src.core.chat_engine import ChatEngine
from src.core.config_manager import ConfigManager
from src.core.preset_manager import PresetManager
from src.core.session_manager import SessionManager
from src.core.user_manager import UserManager
from src.interface.ui_protocol import AbstractUI
from src.storage.factory import StorageFactory
from src.ui.tui.chat_view import ChatView
from src.ui.tui.menu_view import MenuView
from src.ui.tui.widgets import console

logger = logging.getLogger("langchain_chat")


class TUIApp(AbstractUI):
    """TUI 主应用程序，管理菜单路由和应用状态"""

    def __init__(self) -> None:
        self.menu = MenuView()
        self.chat = ChatView()
        self._running = False
        self._config: ConfigManager | None = None
        self._storage = None
        self._user_manager: UserManager | None = None
        self._preset_manager: PresetManager | None = None
        self._session_manager: SessionManager | None = None
        self._chat_engine: ChatEngine | None = None

    @property
    def current_user(self) -> dict | None:
        if self._user_manager and self._user_manager.current_user:
            u = self._user_manager.current_user
            return {"id": u.id, "username": u.username, "default_model": u.default_model}
        return None

    @staticmethod
    def _setup_logging() -> None:
        """配置日志系统"""
        os.makedirs("logs", exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("logs/app.log", encoding="utf-8"),
            ],
        )

    async def run(self) -> None:
        """启动 TUI 主循环"""
        # 配置日志
        self._setup_logging()

        self._config = ConfigManager()
        storage_config = self._config.storage_config
        self._storage = StorageFactory.create(
            self._config.storage_type,
            sqlite_path=storage_config.get("sqlite", {}).get("path", "data/sqlite/app.db"),
        )
        await self._storage.initialize()
        self._user_manager = UserManager(self._storage)
        self._preset_manager = PresetManager(self._storage)
        self._session_manager = SessionManager(self._storage)
        self._chat_engine = ChatEngine(self._config)
        await self._preset_manager.load_builtin_presets()

        self._running = True
        try:
            while self._running:
                action = await self.menu.show_main_menu()
                await self._handle_action(action)
        finally:
            await self._storage.close()

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

    def _get_current_user_id(self) -> int | None:
        if self._user_manager and self._user_manager.current_user:
            return self._user_manager.current_user.id
        return None

    # ── 用户管理 ──────────────────────────────────────────

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
            self._preset_manager.user_id = user.id
            self.menu.show_message(f"用户 '{username}' 创建成功，已自动登录", "success")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_switch_user(self) -> None:
        username = await self.menu.get_text_input("请输入要切换的用户名")
        if not username:
            return
        try:
            user = await self._user_manager.switch_user(username)
            self._preset_manager.user_id = user.id
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
            self._preset_manager.user_id = None
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

    # ── 预设管理（Step 5） ────────────────────────────────

    async def _handle_preset_menu(self) -> None:
        while True:
            action = await self.menu.show_preset_menu()
            if action == "back":
                break
            elif action == "list_presets":
                await self._do_list_presets()
            elif action == "select_preset":
                await self._do_select_preset()
            elif action == "create_preset":
                await self._do_create_preset()
            elif action == "edit_preset":
                await self._do_edit_preset()
            elif action == "delete_preset":
                await self._do_delete_preset()

    async def _do_list_presets(self) -> None:
        user_id = self._get_current_user_id()
        self._preset_manager.user_id = user_id
        presets = await self._preset_manager.list_all_presets()
        preset_list = []
        for p in presets:
            preset_list.append({
                "id": str(p.id),
                "name": p.name,
                "description": p.description or "",
                "is_builtin": "系统内置" if p.is_builtin else "自定义",
            })
        self.menu.show_preset_list(preset_list)
        await self._wait_enter()

    async def _do_select_preset(self) -> None:
        if not self._get_current_user_id():
            self.menu.show_message("请先登录用户", "warning")
            return
        user_id = self._get_current_user_id()
        self._preset_manager.user_id = user_id
        presets = await self._preset_manager.list_all_presets()
        if not presets:
            self.menu.show_message("暂无可用预设", "info")
            return

        preset_list = []
        for i, p in enumerate(presets, 1):
            preset_list.append(f"{i}. {p.name}")
        self.menu.show_message("\n".join(preset_list), "info")

        choice = await self.menu.get_text_input("请输入预设编号（输入 0 表示不使用预设）")
        try:
            idx = int(choice)
            if idx == 0:
                self.menu.show_message("已取消选择预设", "info")
                return
            if 1 <= idx <= len(presets):
                p = presets[idx - 1]
                self.menu.show_message(f"当前会话将使用预设: {p.name}", "success")
            else:
                self.menu.show_message("无效的编号", "error")
        except ValueError:
            self.menu.show_message("请输入有效数字", "error")

    async def _do_create_preset(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        name = await self.menu.get_text_input("请输入预设名称")
        if not name:
            return
        description = await self.menu.get_text_input("请输入预设描述（可选）")
        system_prompt = await self.menu.get_text_input("请输入系统提示词 (system prompt)")
        if not system_prompt:
            return
        try:
            self._preset_manager.user_id = user_id
            preset = await self._preset_manager.create_preset(name, description or "", system_prompt)
            self.menu.show_message(f"预设 '{preset.name}' 创建成功", "success")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_edit_preset(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        self._preset_manager.user_id = user_id
        my_presets = await self._preset_manager.list_user_presets()
        if not my_presets:
            self.menu.show_message("你暂无自定义预设", "info")
            return
        for i, p in enumerate(my_presets, 1):
            self.menu.show_message(f"{i}. {p.name}")
        choice = await self.menu.get_text_input("请输入要编辑的预设编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(my_presets):
                p = my_presets[idx - 1]
                name = await self.menu.get_text_input(f"名称 [{p.name}]")
                desc = await self.menu.get_text_input(f"描述 [{p.description}]")
                sp = await self.menu.get_text_input(f"系统提示词 [{p.system_prompt}]")
                updated = await self._preset_manager.update_preset(
                    p.id, name or p.name, desc or p.description, sp or p.system_prompt
                )
                self.menu.show_message(f"预设 '{updated.name}' 更新成功", "success")
            else:
                self.menu.show_message("无效的编号", "error")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    async def _do_delete_preset(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        self._preset_manager.user_id = user_id
        my_presets = await self._preset_manager.list_user_presets()
        if not my_presets:
            self.menu.show_message("你暂无自定义预设", "info")
            return
        for i, p in enumerate(my_presets, 1):
            self.menu.show_message(f"{i}. {p.name}")
        choice = await self.menu.get_text_input("请输入要删除的预设编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(my_presets):
                p = my_presets[idx - 1]
                confirmed = await self.menu.get_confirmation(f"确定要删除预设 '{p.name}' 吗？")
                if confirmed:
                    await self._preset_manager.delete_preset(p.id)
                    self.menu.show_message(f"预设 '{p.name}' 已删除", "success")
                else:
                    self.menu.show_message("已取消", "info")
            else:
                self.menu.show_message("无效的编号", "error")
        except ValueError as e:
            self.menu.show_message(str(e), "error")

    # ── 核心对话（Step 7 实现） ────────────────────────────

    async def _handle_chat(self) -> None:
        """进入对话模式"""
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先创建或选择用户", "warning")
            return

        # 创建新会话
        current_model = self._user_manager.current_user.default_model
        session = await self._session_manager.create_session(
            user_id=user_id,
            model_name=current_model,
        )

        # 初始化对话引擎
        self._chat_engine.clear_history()
        self._chat_engine.set_model(current_model)

        await self.chat.start_chat_view(session.title)
        await self.chat.display_info("进入对话模式，输入消息开始对话，输入 /quit 退出对话")

        # 对话循环
        while self._running:
            user_msg = await self.chat.get_user_message()
            if not user_msg:
                continue

            # 处理内置命令
            if user_msg == "/quit":
                break
            elif user_msg == "/help":
                await self.chat.display_help()
                continue
            elif user_msg == "/new":
                await self.chat.display_info("返回主菜单新建会话...")
                break

            # 显示用户消息
            await self.chat.display_user_message(user_msg)

            # 保存用户消息
            await self._session_manager.save_message(role="human", content=user_msg)

            # 调用 LLM 流式输出
            try:
                console.print()
                console.print("[bold cyan]AI:[/bold cyan]")

                full_response = ""
                async for chunk in self._chat_engine.stream_chat(user_msg):
                    full_response += chunk
                    console.print(chunk, end="")
                console.print("\n")

                # 保存 AI 回复
                if full_response:
                    await self._session_manager.save_message(
                        role="ai",
                        content=full_response,
                        prompt_tokens=self._chat_engine.total_prompt_tokens,
                        completion_tokens=self._chat_engine.total_completion_tokens,
                    )

                # 显示 Token 用量
                await self.chat.display_token_usage(
                    self._chat_engine.total_prompt_tokens,
                    self._chat_engine.total_completion_tokens,
                    self._session_manager.current_session.total_prompt_tokens,
                    self._session_manager.current_session.total_completion_tokens,
                )
            except Exception as e:
                await self.chat.display_error(f"LLM 调用失败: {str(e)}")

        self.menu.show_message("对话已结束", "info")
        await self._wait_enter()

    # ── 会话管理（Step 7-8） ──────────────────────────────

    async def _handle_session_menu(self) -> None:
        while True:
            action = await self.menu.show_session_menu()
            if action == "back":
                break
            elif action == "new_session":
                await self._handle_chat()
            elif action == "load_session":
                await self._do_load_session()
            elif action == "list_sessions":
                await self._do_list_sessions()
            elif action == "rename_session":
                await self._do_rename_session()
            elif action == "delete_session":
                await self._do_delete_session()

    async def _do_load_session(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        sessions = await self._session_manager.list_user_sessions(user_id)
        if not sessions:
            self.menu.show_message("暂无历史会话", "info")
            return
        session_list = []
        for i, s in enumerate(sessions, 1):
            session_list.append(f"{i}. [{s.id}] {s.title} ({s.model_name}) {str(s.updated_at)[:19]}")
        self.menu.show_message("\n".join(session_list), "info")
        choice = await self.menu.get_text_input("请输入会话编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(sessions):
                s = sessions[idx - 1]
                await self._session_manager.load_session(s.id)
                messages = await self._session_manager.get_session_messages(s.id)

                # 恢复对话引擎历史
                self._chat_engine.clear_history()
                self._chat_engine.set_model(s.model_name)
                history = [{"role": m.role, "content": m.content} for m in messages]
                self._chat_engine.restore_history(history)

                # 进入对话
                await self.chat.start_chat_view(s.title)
                await self.chat.display_info(f"已加载会话: {s.title}")

                while self._running:
                    user_msg = await self.chat.get_user_message()
                    if not user_msg:
                        continue
                    if user_msg == "/quit":
                        break
                    elif user_msg == "/help":
                        await self.chat.display_help()
                        continue
                    elif user_msg == "/new":
                        break

                    await self.chat.display_user_message(user_msg)
                    await self._session_manager.save_message(role="human", content=user_msg)

                    try:
                        console.print("[bold cyan]AI:[/bold cyan]")
                        full_response = ""
                        async for chunk in self._chat_engine.stream_chat(user_msg):
                            full_response += chunk
                            console.print(chunk, end="")
                        console.print("\n")

                        if full_response:
                            await self._session_manager.save_message(
                                role="ai",
                                content=full_response,
                                prompt_tokens=self._chat_engine.total_prompt_tokens,
                                completion_tokens=self._chat_engine.total_completion_tokens,
                            )
                        await self.chat.display_token_usage(
                            self._chat_engine.total_prompt_tokens,
                            self._chat_engine.total_completion_tokens,
                            self._session_manager.current_session.total_prompt_tokens,
                            self._session_manager.current_session.total_completion_tokens,
                        )
                    except Exception as e:
                        await self.chat.display_error(f"LLM 调用失败: {str(e)}")
            else:
                self.menu.show_message("无效的编号", "error")
        except ValueError:
            self.menu.show_message("请输入有效数字", "error")

    async def _do_list_sessions(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        sessions = await self._session_manager.list_user_sessions(user_id)
        session_list = []
        for s in sessions:
            session_list.append({
                "id": str(s.id),
                "title": s.title,
                "model_name": s.model_name,
                "created_at": str(s.created_at)[:19] if s.created_at else "",
                "updated_at": str(s.updated_at)[:19] if s.updated_at else "",
            })
        self.menu.show_session_list(session_list)
        await self._wait_enter()

    async def _do_rename_session(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        sessions = await self._session_manager.list_user_sessions(user_id)
        if not sessions:
            self.menu.show_message("暂无历史会话", "info")
            return
        for i, s in enumerate(sessions, 1):
            self.menu.show_message(f"{i}. [{s.id}] {s.title}")
        choice = await self.menu.get_text_input("请输入要重命名的会话编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(sessions):
                s = sessions[idx - 1]
                new_title = await self.menu.get_text_input("请输入新标题")
                if new_title:
                    await self._session_manager.rename_session(s.id, new_title)
                    self.menu.show_message(f"会话已重命名为: {new_title}", "success")
        except ValueError:
            self.menu.show_message("请输入有效数字", "error")

    async def _do_delete_session(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        sessions = await self._session_manager.list_user_sessions(user_id)
        if not sessions:
            self.menu.show_message("暂无历史会话", "info")
            return
        for i, s in enumerate(sessions, 1):
            self.menu.show_message(f"{i}. [{s.id}] {s.title}")
        choice = await self.menu.get_text_input("请输入要删除的会话编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(sessions):
                s = sessions[idx - 1]
                confirmed = await self.menu.get_confirmation(f"确定要删除会话 '{s.title}' 及其所有消息吗？")
                if confirmed:
                    await self._session_manager.delete_session(s.id)
                    self.menu.show_message(f"会话 '{s.title}' 已删除", "success")
        except ValueError:
            self.menu.show_message("请输入有效数字", "error")

    # ── 搜索（Step 9 桩） ─────────────────────────────────

    async def _handle_search(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        keyword = await self.menu.get_text_input("请输入搜索关键词")
        if not keyword:
            return
        results = await self._session_manager.search_messages(user_id, keyword)
        if not results:
            self.menu.show_message("未找到匹配的消息", "info")
        else:
            for r in results:
                role = "用户" if r.get("role") == "human" else "AI"
                self.menu.show_message(f"[{r['id']}] {role} | 会话: {r.get('session_title', '')}")
                self.menu.show_message(f"  {r.get('content', '')[:100]}")
        await self._wait_enter()

    # ── 导出（Step 10 桩） ────────────────────────────────

    async def _handle_export(self) -> None:
        user_id = self._get_current_user_id()
        if not user_id:
            self.menu.show_message("请先登录用户", "warning")
            return
        sessions = await self._session_manager.list_user_sessions(user_id)
        if not sessions:
            self.menu.show_message("暂无历史会话", "info")
            return
        for i, s in enumerate(sessions, 1):
            self.menu.show_message(f"{i}. [{s.id}] {s.title}")
        choice = await self.menu.get_text_input("请输入要导出的会话编号")
        try:
            idx = int(choice)
            if 1 <= idx <= len(sessions):
                s = sessions[idx - 1]
                filepath = await self._session_manager.export_session_to_markdown(s.id)
                self.menu.show_message(f"已导出到: {filepath}", "success")
        except ValueError:
            self.menu.show_message("请输入有效数字", "error")
        await self._wait_enter()

    # ── 模型设置（Step 10 桩） ────────────────────────────

    async def _handle_model_settings(self) -> None:
        models = self._config.available_models
        self.menu.show_message("可用模型列表:", "info")
        for i, m in enumerate(models, 1):
            current = " (当前)" if m == self._chat_engine.model_name else ""
            self.menu.show_message(f"  {i}. {m}{current}")
        choice = await self.menu.get_text_input("输入编号切换模型（回车返回）")
        if choice:
            try:
                idx = int(choice)
                if 1 <= idx <= len(models):
                    new_model = models[idx - 1]
                    self._chat_engine.set_model(new_model)
                    if self._user_manager.current_user:
                        self._user_manager.current_user.default_model = new_model
                        await self._user_manager.update_user(self._user_manager.current_user)
                    self.menu.show_message(f"已切换到模型: {new_model}", "success")
                else:
                    self.menu.show_message("无效的编号", "error")
            except ValueError:
                self.menu.show_message("请输入有效数字", "error")
        await self._wait_enter()

    async def _handle_settings(self) -> None:
        self.menu.show_message("系统设置功能将在后续步骤实现", "info")

    async def _handle_quit(self) -> None:
        self._running = False
        self.menu.show_message("再见！", "success")

    async def _wait_enter(self) -> None:
        await self.menu.get_text_input("按回车键继续")

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
