"""配置管理器 —— 加载 .env + config.yaml + logging.yaml"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigManager:
    """统一配置管理：环境变量 + YAML 配置 + 日志配置"""

    def __init__(self, config_dir: str = ".") -> None:
        self._config_dir = Path(config_dir)
        self._config: dict[str, Any] = {}
        self._logging_config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """加载所有配置"""
        # 1. 加载 .env 环境变量
        env_path = self._config_dir / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        # 2. 加载 config.yaml
        config_path = self._config_dir / "config.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

        # 3. 加载 config/logging.yaml
        logging_path = self._config_dir / "config" / "logging.yaml"
        if logging_path.exists():
            with open(logging_path, "r", encoding="utf-8") as f:
                self._logging_config = yaml.safe_load(f) or {}

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
        """返回原始配置字典"""
        return self._config
