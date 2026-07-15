"""对话引擎单元测试"""

import pytest

from src.core.chat_engine import ChatEngine
from src.models.schemas import TokenUsage


class FakeConfig:
    """ChatEngine 测试用的假配置"""

    def __init__(self) -> None:
        self.api_base_url = "https://fake.api/v1"
        self.api_key = "fake-key"
        self.model_name = "fake-model"
        self.llm_temperature = 0.7
        self.llm_max_tokens = 4096
        self.llm_timeout = 30
        self.llm_max_retries = 1
        self.max_context_messages = 40


class TestChatEngineBasic:
    """ChatEngine 基础功能测试（不调用 LLM）"""

    def test_init(self) -> None:
        config = FakeConfig()
        engine = ChatEngine(config)
        assert engine.model_name == "fake-model"
        assert engine.messages == []
        assert engine.total_prompt_tokens == 0
        assert engine.total_completion_tokens == 0

    def test_set_system_prompt(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.set_system_prompt("你是一个助手")
        assert engine._system_prompt == "你是一个助手"

    def test_clear_system_prompt(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.set_system_prompt("你是一个助手")
        engine.set_system_prompt(None)
        assert engine._system_prompt is None

    def test_set_model(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.set_model("new-model")
        assert engine.model_name == "new-model"

    def test_clear_history(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.add_user_message("hello")
        engine.add_ai_message("hi")
        assert len(engine.messages) == 2
        engine.clear_history()
        assert engine.messages == []
        assert engine.total_prompt_tokens == 0
        assert engine.total_completion_tokens == 0
        assert engine._last_prompt_tokens == 0
        assert engine._last_completion_tokens == 0

    def test_add_user_message(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.add_user_message("test")
        assert len(engine.messages) == 1
        from langchain_core.messages import HumanMessage

        assert isinstance(engine.messages[0], HumanMessage)
        assert engine.messages[0].content == "test"

    def test_add_ai_message(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.add_ai_message("response")
        assert len(engine.messages) == 1
        from langchain_core.messages import AIMessage

        assert isinstance(engine.messages[0], AIMessage)
        assert engine.messages[0].content == "response"

    def test_get_history_as_dicts(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.add_user_message("Q1")
        engine.add_ai_message("A1")
        history = engine.get_history_as_dicts()
        assert len(history) == 2
        assert history[0] == {"role": "human", "content": "Q1"}
        assert history[1] == {"role": "ai", "content": "A1"}
        # system prompt not in history when not set
        engine.set_system_prompt("system msg")
        history2 = engine.get_history_as_dicts()
        assert len(history2) == 2  # system prompt stored separately, not in messages

    def test_restore_history(self) -> None:
        engine = ChatEngine(FakeConfig())
        history = [
            {"role": "human", "content": "Q1"},
            {"role": "ai", "content": "A1"},
            {"role": "human", "content": "Q2"},
            {"role": "ai", "content": "A2"},
        ]
        engine.restore_history(history)
        assert len(engine.messages) == 4
        assert engine.get_history_as_dicts() == history

    def test_restore_history_with_system(self) -> None:
        engine = ChatEngine(FakeConfig())
        history = [
            {"role": "system", "content": "你是一个专家"},
            {"role": "human", "content": "Q1"},
            {"role": "ai", "content": "A1"},
        ]
        engine.restore_history(history)
        assert engine._system_prompt == "你是一个专家"
        assert len(engine.messages) == 2

    def test_get_last_usage_default(self) -> None:
        engine = ChatEngine(FakeConfig())
        usage = engine.get_last_usage()
        assert isinstance(usage, TokenUsage)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_build_messages_for_api(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.set_system_prompt("system msg")
        engine.add_user_message("hello")
        api_messages = engine._build_messages_for_api()
        assert len(api_messages) == 2
        from langchain_core.messages import SystemMessage

        assert isinstance(api_messages[0], SystemMessage)
        assert api_messages[0].content == "system msg"

    def test_build_messages_no_system(self) -> None:
        engine = ChatEngine(FakeConfig())
        engine.add_user_message("hello")
        api_messages = engine._build_messages_for_api()
        assert len(api_messages) == 1

    def test_sliding_window_context_trim(self) -> None:
        """测试滑动窗口裁剪"""
        config = FakeConfig()
        config.max_context_messages = 4
        engine = ChatEngine(config)
        # 添加 6 条消息（超过窗口大小）
        for i in range(6):
            engine.add_user_message(f"Q{i}")
            engine.add_ai_message(f"A{i}")
        assert len(engine.messages) == 12

        # 模拟 stream_chat 中的裁剪逻辑
        engine.add_user_message("overflow trigger")
        assert len(engine.messages) > engine._max_context_messages
        overflow = len(engine.messages) - engine._max_context_messages
        engine._messages = engine._messages[overflow:]
        assert len(engine.messages) == engine._max_context_messages
