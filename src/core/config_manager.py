"""配置管理器 —— 加载 .env + config.yaml + 环境覆盖 + logging.yaml

支持通过 APP_ENV 环境变量切换运行环境（dev/test/prod）。
配置合并策略：config.yaml（基础）→ config.{env}.yaml（覆盖）
"""

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

logger = logging.getLogger("langchain_chat")


class ConfigManager:
    """统一配置管理：环境变量 + YAML 多环境配置 + 日志配置"""

    def __init__(self, config_dir: str = ".", app_env: str | None = None) -> None:
        self._config_dir = Path(config_dir)
        self._app_env = app_env or os.getenv("APP_ENV", "dev")
        self._config: dict[str, Any] = {}
        self._logging_config: dict[str, Any] = {}
        self._load()

    @property
    def app_env(self) -> str:
        return self._app_env

    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并两个字典，override 覆盖 base"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _load(self) -> None:
        """加载所有配置，按优先级合并"""
        # 1. 加载 .env 环境变量（根据 APP_ENV 选择）
        # 优先级: .env.{env} > .env
        env_specific = self._config_dir / f".env.{self._app_env}"
        if env_specific.exists():
            load_dotenv(env_specific)
        else:
            dotenv_path = self._config_dir / ".env"
            if dotenv_path.exists():
                load_dotenv(dotenv_path)
            else:
                load_dotenv()

        # 2. 加载基础 config.yaml
        config_path = self._config_dir / "config.yaml"
        base_config: dict[str, Any] = {}
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}

        # 3. 加载环境覆盖 config.{env}.yaml
        env_config_path = self._config_dir / f"config.{self._app_env}.yaml"
        env_config: dict[str, Any] = {}
        if env_config_path.exists():
            with open(env_config_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}

        # 4. 深度合并
        self._config = self._deep_merge(base_config, env_config)
        logger.info("加载配置: APP_ENV=%s, storage_type=%s", self._app_env,
                      self._config.get("storage", {}).get("type", "unknown"))

        # 5. 加载 config/logging.yaml
        logging_path = self._config_dir / "config" / "logging.yaml"
        if logging_path.exists():
            with open(logging_path, "r", encoding="utf-8") as f:
                self._logging_config = yaml.safe_load(f) or {}

        # 6. 确保数据目录存在
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """确保数据目录存在"""
        sqlite_path = self._config.get("storage", {}).get("sqlite", {}).get("path", "")
        if sqlite_path:
            os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)

    # ── 便捷属性 ──────────────────────────────────────────

    @property
    def api_base_url(self) -> str:
        return os.getenv("API_BASE_URL", "https://api.openai.com/v1")

    @property
    def api_key(self) -> str:
        return os.getenv("API_KEY", "")

    @property
    def model_name(self) -> str:
        return os.getenv("MODEL_NAME", self._config.get("llm", {}).get("default_model", "gpt-4o-mini"))

    @property
    def available_models(self) -> list[str]:
        return self._config.get("llm", {}).get("available_models", ["gpt-4o-mini"])

    @property
    def llm_timeout(self) -> int:
        return self._config.get("llm", {}).get("timeout", 60)

    @property
    def llm_max_retries(self) -> int:
        return self._config.get("llm", {}).get("max_retries", 3)

    @property
    def llm_temperature(self) -> float:
        return self._config.get("llm", {}).get("temperature", 0.7)

    @property
    def llm_max_tokens(self) -> int:
        return self._config.get("llm", {}).get("max_tokens", 4096)

    @property
    def storage_type(self) -> str:
        return self._config.get("storage", {}).get("type", "sqlite")

    @property
    def storage_config(self) -> dict[str, Any]:
        return self._config.get("storage", {})

    @property
    def auto_title_max_length(self) -> int:
        return self._config.get("session", {}).get("auto_title_max_length", 30)

    @property
    def max_context_messages(self) -> int:
        return self._config.get("session", {}).get("max_context_messages", 40)

    @property
    def export_base_path(self) -> str:
        return self._config.get("export", {}).get("base_path", "data/users")

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取嵌套配置，支持点号分隔，如 'llm.timeout'"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def get_logging_config(self) -> dict[str, Any]:
        """返回日志配置字典"""
        return self._logging_config

    @property
    def config(self) -> dict[str, Any]:
        """返回合并后的完整配置字典"""
        return self._config
