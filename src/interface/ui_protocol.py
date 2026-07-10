"""UI 协议接口 + 扩展预留接口"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional


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


# ═══════════════════════════════════════════════════════════════
# 以下为后期预留接口（当前阶段仅定义接口，不实现）
# 详见：需求1.md 第三-H 节
# ═══════════════════════════════════════════════════════════════


class MultiModelRunner(ABC):
    """多模型并行对比接口（H2，后期实现）

    同一 prompt 同时发送给多个模型，对比展示输出结果。
    """

    @abstractmethod
    async def run_parallel(
        self, prompt: str, models: list[str]
    ) -> dict[str, str]:
        """并行调用多个模型，返回 {model_name: response_text}"""
        ...

    @abstractmethod
    async def run_sequential(
        self, prompt: str, models: list[str]
    ) -> AsyncIterator[tuple[str, str]]:
        """顺序调用多个模型，逐个产出 (model_name, response_text)"""
        ...


class MultimodalInput(ABC):
    """多模态输入接口（H3，后期实现）

    支持图片、文件上传及解析。
    """

    @abstractmethod
    async def upload_image(self, file_path: str) -> str:
        """上传图片并返回 base64 编码或 URL"""
        ...

    @abstractmethod
    async def upload_file(self, file_path: str) -> str:
        """上传文件并返回解析后的文本内容"""
        ...

    @abstractmethod
    async def parse_document(self, file_path: str) -> str:
        """解析文档（PDF/Word/TXT）返回纯文本"""
        ...


class AudioProcessor(ABC):
    """语音处理接口（H4，后期实现）

    语音转文字（STT）和文字转语音（TTS）。
    """

    @abstractmethod
    async def speech_to_text(self, audio_path: str) -> str:
        """语音转文字"""
        ...

    @abstractmethod
    async def text_to_speech(self, text: str, output_path: str) -> str:
        """文字转语音，返回音频文件路径"""
        ...

    @abstractmethod
    async def stream_text_to_speech(
        self, text_stream: AsyncIterator[str]
    ) -> AsyncIterator[bytes]:
        """流式文字转语音，逐块产出音频数据"""
        ...


class ToolManager(ABC):
    """Agent 工具调用接口（H5，后期实现）

    Agent/Tool 扩展框架：函数调用、外部工具集成。
    """

    @abstractmethod
    async def register_tool(self, name: str, func: callable, description: str) -> None:
        """注册一个工具"""
        ...

    @abstractmethod
    async def unregister_tool(self, name: str) -> None:
        """注销一个工具"""
        ...

    @abstractmethod
    async def list_tools(self) -> list[dict]:
        """列出所有已注册工具"""
        ...

    @abstractmethod
    async def execute_tool(self, name: str, **kwargs) -> Any:
        """执行指定工具并返回结果"""
        ...
