"""对话引擎 —— LLM 调用、Memory、流式输出、超时重试、Token 统计"""

import asyncio
from typing import AsyncIterator, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.core.config_manager import ConfigManager
from src.models.schemas import TokenUsage


class ChatEngine:
    """对话引擎，封装 LLM 调用、上下文管理和流式输出"""

    def __init__(self, config: ConfigManager) -> None:
        self._config = config
        self._messages: list = []  # 当前会话的消息历史
        self._system_prompt: Optional[str] = None
        self._model_name: str = config.model_name
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def messages(self) -> list:
        return self._messages

    @property
    def total_prompt_tokens(self) -> int:
        return self._total_prompt_tokens

    @property
    def total_completion_tokens(self) -> int:
        return self._total_completion_tokens

    def set_system_prompt(self, prompt: Optional[str]) -> None:
        """设置系统提示词（预设角色）"""
        self._system_prompt = prompt

    def set_model(self, model_name: str) -> None:
        """切换模型"""
        self._model_name = model_name

    def clear_history(self) -> None:
        """清空对话历史"""
        self._messages.clear()
        self._total_prompt_tokens = 0
        self._total_completion_tokens = 0

    def add_user_message(self, content: str) -> None:
        """添加用户消息到历史"""
        self._messages.append(HumanMessage(content=content))

    def add_ai_message(self, content: str) -> None:
        """添加 AI 消息到历史"""
        self._messages.append(AIMessage(content=content))

    def _build_llm(self) -> ChatOpenAI:
        """构建 ChatOpenAI 实例"""
        return ChatOpenAI(
            base_url=self._config.api_base_url,
            api_key=self._config.api_key,
            model=self._model_name,
            temperature=self._config.llm_temperature,
            max_tokens=self._config.llm_max_tokens,
            timeout=self._config.llm_timeout,
            max_retries=self._config.llm_max_retries,
            streaming=True,
        )

    def _build_messages_for_api(self) -> list:
        """构建发送给 API 的消息列表（含系统提示词）"""
        api_messages = []
        if self._system_prompt:
            api_messages.append(SystemMessage(content=self._system_prompt))
        api_messages.extend(self._messages)
        return api_messages

    async def stream_chat(self, user_message: str) -> AsyncIterator[str]:
        """流式对话：发送用户消息，逐 token 产出 AI 回复"""
        self.add_user_message(user_message)
        llm = self._build_llm()
        api_messages = self._build_messages_for_api()

        full_content = ""
        usage = None
        async for chunk in llm.astream(api_messages):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                full_content += content
                yield content
            if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                usage = chunk.usage_metadata

        if full_content:
            self.add_ai_message(full_content)

            if usage and usage.get("input_tokens"):
                prompt_tokens = usage.get("input_tokens", 0)
                completion_tokens = usage.get("output_tokens", 0)
            else:
                prompt_chars = sum(len(m.content) if hasattr(m, "content") else 0 for m in api_messages)
                completion_chars = len(full_content)
                prompt_tokens = max(1, prompt_chars // 2)
                completion_tokens = max(1, completion_chars // 2)

            self._total_prompt_tokens += prompt_tokens
            self._total_completion_tokens += completion_tokens

    async def chat(self, user_message: str) -> str:
        """非流式对话：发送用户消息，返回完整 AI 回复"""
        full_content = ""
        async for chunk in self.stream_chat(user_message):
            full_content += chunk
        return full_content

    def get_last_usage(self) -> TokenUsage:
        """获取最近一轮的 Token 用量估计"""
        # 返回累计用量
        return TokenUsage(
            prompt_tokens=self._total_prompt_tokens,
            completion_tokens=self._total_completion_tokens,
            total_tokens=self._total_prompt_tokens + self._total_completion_tokens,
        )

    def get_history_as_dicts(self) -> list[dict]:
        """获取对话历史，返回 [{'role': ..., 'content': ...}, ...]"""
        result = []
        for m in self._messages:
            role = "system"
            if isinstance(m, HumanMessage):
                role = "human"
            elif isinstance(m, AIMessage):
                role = "ai"
            elif isinstance(m, SystemMessage):
                role = "system"
            result.append({"role": role, "content": m.content if hasattr(m, "content") else str(m)})
        return result

    def restore_history(self, history: list[dict]) -> None:
        """从存储恢复对话历史"""
        self._messages.clear()
        for m in history:
            role = m.get("role", "")
            content = m.get("content", "")
            if role == "human":
                self._messages.append(HumanMessage(content=content))
            elif role == "ai":
                self._messages.append(AIMessage(content=content))
            elif role == "system":
                self._system_prompt = content
