"""Pydantic 数据模型定义 —— User, Session, Message, Preset, UserConfig"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """用户模型"""
    id: Optional[int] = None
    username: str = Field(..., min_length=1, max_length=50)
    default_model: str = "gpt-4o-mini"
    default_preset_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Session(BaseModel):
    """会话模型"""
    id: Optional[int] = None
    user_id: int
    title: str = "新对话"
    model_name: str = "gpt-4o-mini"
    preset_id: Optional[int] = None
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Message(BaseModel):
    """消息模型"""
    id: Optional[int] = None
    session_id: int
    role: str  # human / ai / system
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class Preset(BaseModel):
    """预设角色模型"""
    id: Optional[int] = None
    user_id: Optional[int] = None  # NULL 表示系统内置
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    system_prompt: str = ""
    is_builtin: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class UserConfig(BaseModel):
    """用户配置键值对"""
    id: Optional[int] = None
    user_id: int
    key: str
    value: str
    updated_at: datetime = Field(default_factory=datetime.now)


class TokenUsage(BaseModel):
    """Token 用量统计"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
