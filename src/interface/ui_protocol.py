"""UI 协议接口 —— TUI / WebUI 共同遵守的接口规范"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class AbstractUI(ABC):
    """UI 抽象基类，TUI 和 WebUI 必须实现此接口"""

    @abstractmethod
    async def run(self) -> None:
        """启动 UI 主循环"""
        ...

    @abstractmethod
    async def display_message(self, content: str, role: str = "ai") -> None:
        """显示一条消息"""
        ...

    @abstractmethod
    async def display_stream(self, chunk: str) -> None:
        """流式显示内容片段"""
        ...

    @abstractmethod
    async def display_error(self, message: str) -> None:
        """显示错误信息"""
        ...

    @abstractmethod
    async def display_info(self, message: str) -> None:
        """显示提示信息"""
        ...

    @abstractmethod
    async def get_input(self, prompt: str = "> ") -> str:
        """获取用户文本输入"""
        ...

    @abstractmethod
    async def get_confirmation(self, prompt: str) -> bool:
        """获取用户确认（是/否）"""
        ...

    @abstractmethod
    async def show_menu(self, title: str, options: list[str]) -> int:
        """显示菜单并返回用户选择索引"""
        ...

    @abstractmethod
    async def show_table(self, title: str, headers: list[str], rows: list[list[str]]) -> None:
        """显示表格数据"""
        ...
