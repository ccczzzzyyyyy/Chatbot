# LangChain Chat

基于 LangChain 的多轮会话系统，支持多用户、多会话、预设角色、流式对话、Markdown 导出等功能。

## 功能特性

### 核心对话
- 多轮流式对话，基于 LangChain ChatOpenAI
- 全链路异步架构（asyncio）
- 可配置 LLM 后端（兼容 OpenAI API 的任何服务）
- 会话内模型切换

### 用户系统
- 多用户创建/切换/删除
- 用户数据完全隔离

### 会话管理
- 新建/加载/重命名/删除会话
- 首轮对话自动生成标题
- 每轮对话自动持久化保存

### 预设 Prompt
- 5 种系统内置预设（翻译助手、代码专家、创意写手、英语老师、通用助手）
- 用户自定义预设 CRUD

### 搜索与统计
- 关键词搜索历史消息
- Token 用量实时统计

### 导出
- 对话导出为 Markdown 文件

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| LLM 框架 | LangChain + langchain-openai | >=1.3.11 |
| 语言 | Python | >=3.10 |
| 异步 | asyncio | — |
| 存储 | SQLite / MySQL / File | 可切换 |
| TUI | Rich + prompt_toolkit | — |
| 数据模型 | Pydantic | >=2.0 |
| 配置 | YAML + .env | — |
| 测试 | pytest + pytest-asyncio | — |

## 快速开始

```bash
# 1. 安装 uv（如未安装）
pip install uv

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入真实的 API_BASE_URL、API_KEY、MODEL_NAME

# 4. 初始化数据库
uv run python scripts/init_db.py

# 5. 启动程序
uv run python src/main.py

# 6. 运行测试
uv run pytest tests/ -v
```

## 项目结构

```
langchain-chat/
├── config/                  # 配置文件
│   ├── presets.yaml         # 系统内置预设 Prompt
│   └── logging.yaml         # 日志配置
├── docs/
│   └── architecture.md      # 架构设计说明
├── src/
│   ├── main.py              # 程序入口
│   ├── core/                # 核心业务层
│   │   ├── chat_engine.py   # LLM 对话引擎
│   │   ├── user_manager.py  # 用户管理
│   │   ├── session_manager.py # 会话管理
│   │   ├── preset_manager.py  # 预设管理
│   │   └── config_manager.py  # 配置管理
│   ├── models/
│   │   └── schemas.py       # Pydantic 数据模型
│   ├── storage/             # 可插拔存储层
│   │   ├── base.py          # 抽象接口
│   │   ├── factory.py       # 工厂模式
│   │   ├── sqlite_backend.py
│   │   ├── mysql_backend.py
│   │   └── file_backend.py
│   ├── interface/
│   │   └── ui_protocol.py   # UI 协议 + 扩展预留接口
│   └── ui/tui/              # TUI 界面
│       ├── app.py           # 主应用
│       ├── menu_view.py     # 菜单视图
│       ├── chat_view.py     # 对话视图
│       └── widgets.py       # 复用组件
├── tests/                   # 测试
├── scripts/init_db.py       # 数据库初始化
├── config.yaml              # 全局配置
├── .env.example             # 环境变量模板
└── pyproject.toml           # 项目元数据
```

## 配置说明

### 存储切换

修改 `config.yaml`：

```yaml
storage:
  type: sqlite   # sqlite | mysql | file
```

### 模型配置

通过 `.env` 配置 LLM 后端：

```
API_BASE_URL=https://api.openai.com/v1
API_KEY=sk-your-key
MODEL_NAME=gpt-4o-mini
```

### 环境切换（Step 15）

```
APP_ENV=dev uv run python src/main.py
APP_ENV=test uv run pytest
APP_ENV=prod uv run python src/main.py
```

## Git 版本回退

```bash
# 查看所有版本标签
git tag

# 回退到任意步骤
git checkout step-7-first-chat

# 回到最新
git checkout master
```

## 扩展预留

- WebUI 接口（`AbstractUI` 协议已定义）
- 多模型并行对比（`MultiModelRunner` 接口已定义）
- 多模态输入（`MultimodalInput` 接口已定义）
- 语音处理（`AudioProcessor` 接口已定义）
- Tool Calling（`ToolManager` 接口已定义）
