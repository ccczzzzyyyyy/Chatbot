# LangChain Chat

基于 LangChain 的多轮会话系统，支持多用户、多会话、预设角色、流式对话等功能。

## 技术栈

- **框架**: LangChain + langchain-openai
- **语言**: Python 3.10+
- **异步**: 全链路 asyncio
- **存储**: SQLite (默认) / MySQL / File
- **TUI**: Rich + prompt_toolkit
- **配置**: Pydantic + YAML + .env

## 快速开始

```bash
# 1. 安装 uv (如未安装)
pip install uv

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key 等信息

# 4. 启动程序
uv run python src/main.py
```

## 项目结构

```
langchain-chat/
├── config/                 # 配置文件
│   ├── presets.yaml        # 系统内置预设
│   └── logging.yaml        # 日志配置
├── src/                    # 源码
│   ├── core/               # 核心业务层
│   ├── models/             # 数据模型层
│   ├── storage/            # 存储层
│   ├── interface/          # 接口定义层
│   └── ui/                 # UI 实现层
├── tests/                  # 测试
└── data/                   # 运行时数据
```
