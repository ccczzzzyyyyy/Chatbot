"""对话视图 —— 用户输入、流式显示、Token 统计展示"""

from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from src.ui.tui.widgets import console, format_token_usage, print_error, print_info, print_title


class ChatView:
    """对话视图，负责对话交互的展示"""

    def __init__(self) -> None:
        self._history = InMemoryHistory()

    async def start_chat_view(self, session_title: str) -> None:
        """进入对话界面"""
        print_title(f"对话 - {session_title}")
        print_info("输入消息开始对话，输入 /quit 退出对话，输入 /help 查看命令")

    async def get_user_message(self) -> str:
        """获取用户输入的消息"""
        try:
            msg = prompt("你: ", history=self._history, multiline=False)
            return msg.strip()
        except (EOFError, KeyboardInterrupt):
            return "/quit"

    async def display_user_message(self, content: str) -> None:
        """显示用户消息"""
        console.print()
        console.print(Panel(Text(content, style="green"), title="你", border_style="green"))

    async def display_ai_stream(self, stream) -> str:
        """流式显示 AI 回复，返回完整内容"""
        full_content = ""
        console.print()
        console.print("[bold cyan]AI:[/bold cyan]")

        async for chunk in stream:
            full_content += chunk
            console.print(chunk, end="")

        console.print()
        console.print()
        return full_content

    async def display_ai_message(self, content: str) -> None:
        """显示完整的 AI 消息（Markdown 渲染）"""
        console.print()
        md = Markdown(content)
        console.print(Panel(md, title="AI", border_style="cyan"))

    async def display_token_usage(self, prompt_tokens: int, completion_tokens: int, session_total_prompt: int = 0, session_total_completion: int = 0) -> None:
        """显示 Token 用量统计"""
        info = format_token_usage(prompt_tokens, completion_tokens)
        if session_total_prompt or session_total_completion:
            info += f" | 会话累计: prompt={session_total_prompt}, completion={session_total_completion}"
        console.print(Text(info, style="dim"))

    async def display_error(self, message: str) -> None:
        """显示错误信息"""
        print_error(message)

    async def display_info(self, message: str) -> None:
        """显示提示信息"""
        print_info(message)

    async def display_help(self) -> None:
        """显示帮助信息"""
        console.print()
        console.print("[bold]可用命令:[/bold]")
        console.print("  /quit    - 退出当前对话")
        console.print("  /help    - 显示此帮助")
        console.print("  /new     - 新建会话")
        console.print("  /model   - 切换模型")
        console.print("  /export  - 导出当前会话")
        console.print()
