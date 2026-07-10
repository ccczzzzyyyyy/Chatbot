"""TUI 复用组件 —— 样式、格式化、工具函数"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def print_title(text: str) -> None:
    """打印主标题"""
    console.print()
    console.print(Panel(Text(text, style="bold cyan", justify="center"), box=True))


def print_subtitle(text: str) -> None:
    """打印副标题"""
    console.print(Text(text, style="bold yellow"))


def print_success(text: str) -> None:
    """打印成功信息"""
    console.print(Text(f"✓ {text}", style="bold green"))


def print_error(text: str) -> None:
    """打印错误信息"""
    console.print(Text(f"✗ {text}", style="bold red"))


def print_info(text: str) -> None:
    """打印提示信息"""
    console.print(Text(f"ℹ {text}", style="dim"))


def print_warning(text: str) -> None:
    """打印警告信息"""
    console.print(Text(f"⚠ {text}", style="bold yellow"))


def render_markdown(content: str) -> None:
    """渲染 Markdown 内容并打印"""
    md = Markdown(content)
    console.print(md)


def render_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    """渲染表格"""
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for h in headers:
        table.add_column(h, style="white")
    for row in rows:
        table.add_row(*[str(c) for c in row])
    console.print(table)


def format_token_usage(prompt_tokens: int, completion_tokens: int) -> str:
    """格式化 Token 用量信息"""
    total = prompt_tokens + completion_tokens
    return f"Token 用量: prompt={prompt_tokens}, completion={completion_tokens}, total={total}"


def truncate_text(text: str, max_length: int = 30) -> str:
    """截断文本，超过长度加省略号"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
