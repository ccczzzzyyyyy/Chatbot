"""LangChain Chat 项目主入口"""

import asyncio

from src.ui.tui.app import TUIApp


async def main() -> None:
    """程序主入口 —— 启动 TUI 应用"""
    app = TUIApp()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
