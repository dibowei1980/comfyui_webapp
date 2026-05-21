# 项目上下文

## 项目简介
ComfyUI 是一个以节点图为核心的可视化 AI 工作流引擎，支持图像、视频、音频与 3D 生成，并扩展了本地 Web 服务、资产管理、API 节点和插件化自定义节点体系。

## 审查目标
- 优先关注稳定性、向后兼容性、性能、并发安全和资源管理
- 对变更保持最小侵入，避免破坏现有节点接口、自定义节点生态和工作流兼容性
- 审查时优先识别真实新增问题，不重复标注历史遗留问题

# 技术栈

- **语言**: Python 3.10+
- **核心依赖**: torch / torchvision / torchaudio / transformers / numpy / aiohttp / Pillow
- **Web 服务**: aiohttp
- **数据库**: SQLite（默认）+ SQLAlchemy + Alembic
- **配置方式**: CLI 参数、`.env`、`extra_model_paths.yaml`
- **前端资源**: `comfyui-frontend-package`、`comfyui-workflow-templates`、`comfyui-embedded-docs`
- **测试框架**: pytest、pytest-aiohttp、pytest-asyncio、websocket-client
- **静态检查**: Ruff、Pylint
- **类型检查**: 项目内无独立 typecheck 配置，依赖局部类型注解与测试验证
- **容器支持**: Docker、docker-compose

# 代码风格与约定

- **命名风格**:
  - 模块、函数、变量通常使用 `snake_case`
  - 类使用 `PascalCase`
  - 常量使用 `UPPER_SNAKE_CASE`
- **导入顺序**: 一般遵循标准库 → 第三方库 → 项目内模块
- **类型注解**: 局部使用，不要求全量覆盖；新增公共接口时优先补充关键参数和返回值类型
- **文档字符串**: 不强制；已有代码中存在混合风格
- **行宽**: Ruff 已忽略 `E501`，说明没有严格行宽限制，但应保持可读性
- **异常处理**: 项目中允许针对运行时环境做宽松兜底，但新代码应尽量缩小异常范围并保留有效日志
- **日志约定**: 使用 `logging` 或 `app.logger`，不要输出敏感信息、Token、绝对本地隐私路径或外部 API 凭据
- **兼容性原则**: 任何涉及节点输入输出、工作流 JSON、队列协议、Web API、数据库结构的修改，都要先评估兼容性

## Ruff / Pylint 现状
- Ruff 启用 `E/T/W/F` 及部分安全规则，忽略 `E501/E722/E731/E712/E402/E741`
- Pylint 明确关闭了大量历史兼容性相关告警，因此不要机械地按通用最佳实践重写旧代码

# 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务
python main.py

# 监听局域网
python main.py --listen 0.0.0.0 --port 8188

# 启用 manager
python main.py --enable-manager

# Docker 启动
docker compose up --build

# 运行全部测试
pytest

# 运行单元测试
pytest tests-unit/

# 运行推理测试
pytest tests/inference

# Ruff 检查
ruff check .

# Pylint 检查
pylint app comfy comfy_api comfy_execution server.py main.py

# 生成 Alembic 迁移
alembic revision --autogenerate -m "your message"

# 执行迁移
alembic upgrade head
```

# 关键目录

```text
ComfyUI/
├── main.py                    # 主入口，负责参数解析、初始化、启动服务与执行队列
├── server.py                  # aiohttp 服务、WebSocket、HTTP API、中间件
├── nodes.py                   # 核心节点注册与映射
├── execution.py               # 工作流执行、缓存与调度逻辑
├── comfy/                     # 核心模型、采样器、推理与内存管理
├── comfy_execution/           # 图执行、作业、缓存、校验与进度系统
├── comfy_api/                 # 对外 API 与输入输出类型定义
├── comfy_api_nodes/           # 外部服务 API 节点封装
├── comfy_extras/              # 附加节点实现
├── app/                       # 资产、数据库、用户、前端与管理器相关服务
├── api_server/                # 内部 API 路由与服务
├── middleware/                # aiohttp 中间件
├── web/                       # Web 静态页面资源
├── tests/                     # 集成、执行、推理、质量回归测试
├── tests-unit/                # 单元测试
├── alembic_db/                # 数据库迁移脚本
├── blueprints/                # 工作流模板与蓝图
├── script_examples/           # API 使用示例
├── requirements.txt           # 运行依赖
├── pyproject.toml             # 项目元数据、Ruff、Pylint 配置
├── pytest.ini                 # pytest 入口配置
├── docker-compose.yml         # 容器启动配置
└── .env.example               # 模型、输入输出、自定义节点目录映射
```

# 重点审查区域

## 1. `comfy/`
- 这是核心推理与模型加载层
- 重点关注显存管理、热路径性能、设备切换、线程安全
- 对模型加载、采样器和 patcher 的改动必须评估回归风险

## 2. `comfy_execution/`
- 负责图执行、缓存、任务队列、状态与进度
- 重点关注缓存正确性、并发执行安全、图校验边界条件

## 3. `nodes.py` 与 `comfy_extras/`
- 任何节点输入输出签名变更都可能破坏已有工作流和自定义节点
- 审查时优先保证 `INPUT_TYPES`、`RETURN_TYPES`、`FUNCTION`、`CATEGORY` 语义稳定

## 4. `comfy_api_nodes/`
- 涉及外部 API 节点
- 重点检查超时、鉴权、错误处理、用户数据传递安全
- 严禁硬编码密钥或在日志中输出密钥

## 5. `app/`、`api_server/`、`server.py`
- 负责 Web 服务、资产系统、用户目录、内部接口和路由
- 重点检查请求隔离、路径安全、JSON 响应一致性和中间件行为

## 6. `alembic_db/`
- 数据迁移必须保证安全、可升级、尽量可回滚
- 任何 schema 变更都要考虑现有本地数据库文件的升级路径

# 重要约束

## 兼容性
- 尽量不要破坏现有工作流 JSON 格式
- 不要随意修改节点类名、节点映射键、接口字段名
- 自定义节点生态非常重要，核心模块变更需要考虑下游兼容

## 数据库
- 默认数据库为 SQLite，本地文件路径由 `--database-url` 控制
- 应用启动时会自动检查并升级数据库
- 多进程共享同一个 SQLite 文件会触发文件锁冲突，必要时使用独立 `--database-url`
- 内存数据库使用 `sqlite:///:memory:`

## Web 与安全
- `server.py` 中存在 Host / Origin 保护与 CSP 中间件，改动时不要削弱安全边界
- 涉及文件系统路径、上传、下载、用户目录访问时，需要优先考虑路径穿越和越权风险
- 外部 API 节点不得泄露用户内容与凭据

## 资源管理
- GPU / VRAM 管理是核心能力，不能轻易引入额外显存驻留
- 启动阶段存在设备环境变量设置逻辑，避免在错误时机提前导入 torch
- 长时间运行路径需要关注内存泄漏、任务队列堆积和日志膨胀

## 测试策略
- 优先使用现有 pytest 体系验证改动
- 核心逻辑优先补充 `tests-unit/`
- 执行链路、API、队列、进度相关改动优先查看 `tests/execution/`
- 模型推理质量回归可参考 `tests/inference/` 与 `tests/compare/`

# 审查与优化建议

## 进行代码审查时
- 只标记当前改动真正引入的问题
- 不把纯格式化、缩进调整、代码搬移当成逻辑变更
- 先找高影响问题：兼容性、并发、资源管理、安全、数据损坏
- 再看中影响问题：可维护性、重复逻辑、异常边界、日志质量

## 进行代码优化时
- 优先做小步改进，避免一次性大范围重构
- 在热路径上优先减少重复计算、无效拷贝和不必要的模型切换
- 在服务层优先减少不必要的 I/O、重复 JSON 处理和阻塞调用
- 在数据库层优先保证迁移安全和查询正确性，再考虑性能

# 备注

## 运行环境
- `.env.example` 定义了模型、输入、输出、自定义节点、用户目录映射
- Docker 默认将服务暴露在 `8188`
- Windows、Linux、macOS 都是支持平台，但 GPU/驱动差异较大

## 项目特性
- 项目包含大量模型与节点实现，不适合用统一抽象强行“整理”所有历史模块
- 部分功能对外部模型文件、驱动、显卡环境和可选依赖敏感
- 资产系统依赖 SQLAlchemy/Alembic，可在依赖缺失时降级提示

## 建议的 Claude Code 工作方式
- 修改前先确认影响范围属于核心推理、执行引擎、节点接口、Web 服务还是数据库
- 修改后至少运行与改动最相关的 pytest 子集
- 涉及公共接口时，优先补测试而不是仅靠手工推断
- 若发现问题属于历史遗留且不在当前改动范围，单独记录，不阻塞当前最小修复
