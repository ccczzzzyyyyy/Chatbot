# LangChain Chat 架构设计说明

## 一、总体架构

项目采用**分层架构 + 可插拔存储**设计，从下到上分为：

```
┌─────────────────────────────────────┐
│         UI 层 (TUI / WebUI)         │  ← 用户交互
├─────────────────────────────────────┤
│         接口定义层 (UI Protocol)      │  ← TUI/WebUI 共同接口
├─────────────────────────────────────┤
│         核心业务层 (Core)            │  ← 对话引擎、用户、会话、预设
├─────────────────────────────────────┤
│         数据模型层 (Models)          │  ← Pydantic 数据校验
├─────────────────────────────────────┤
│         存储层 (Storage)             │  ← SQLite / MySQL / File
└─────────────────────────────────────┘
```

## 二、核心模块

### 2.1 ChatEngine（对话引擎）

- 基于 LangChain ChatOpenAI 封装
- 支持流式输出（`astream`）
- 自动管理消息历史上下下文
- 超时重试机制
- Token 用量统计

### 2.2 UserManager（用户管理）

- 用户 CRUD
- 多用户数据隔离
- 用户偏好管理

### 2.3 SessionManager（会话管理）

- 会话生命周期（创建/加载/保存）
- 自动标题生成（首条消息前30字符）
- 消息持久化
- 对话搜索
- Markdown 导出

### 2.4 PresetManager（预设管理）

- 系统内置预设（翻译助手、代码专家等）
- 用户自定义预设
- 预设选择与切换

## 三、存储层

### 可插拔设计

通过工厂模式支持三种后端：

| 后端 | 适用场景 |
|------|----------|
| SQLite | 默认，单机开发/小规模使用 |
| MySQL | 企业级多用户部署 |
| File (JSON) | 无数据库环境、轻量使用 |

切换方式：修改 `config.yaml` 中的 `storage.type` 即可。

### 抽象接口

所有后端必须实现 `StorageBackend(ABC)` 中定义的接口：
- User CRUD（6个方法）
- Session CRUD（5个方法）
- Message CRUD（3个方法）
- Preset CRUD（5个方法）
- UserConfig CRUD（3个方法）

## 四、数据流

```
用户输入 → TUI 获取输入
         → ChatEngine.stream_chat() 发送给 LLM
         → LLM 流式返回 tokens
         → TUI 实时渲染显示
         → SessionManager 保存消息到存储
         → Token 用量更新
```

## 五、扩展预留

以下接口已在 `interface/ui_protocol.py` 中预留：

1. **WebUI 接口** — TUI/WebUI 通过实现相同的 `AbstractUI` 接口对接业务层
2. **多模型并行对比** — `MultiModelRunner` 接口，同时调用多个模型对比输出
3. **多模态输入** — `MultimodalInput` 接口，图片/文件上传与解析
4. **语音输入/输出** — `AudioProcessor` 接口，STT/TTS
5. **Tool Calling** — `ToolManager` 接口，Agent 工具调用扩展

## 六、配置体系

```
.env          ← 敏感信息（API Key、数据库密码）
config.yaml   ← 业务配置（模型、存储、会话）
config/logging.yaml ← 日志配置
config/presets.yaml  ← 系统内置预设
```
