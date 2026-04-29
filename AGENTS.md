# AGENTS.md

## 项目架构概述
本项目是一个基于 Python 开发的文本 MUD 游戏，采用典型的**三层架构**：
1.  **表现层 (Presentation)**: `commands.py` 负责解析用户输入并调用引擎接口。
2.  **领域层 (Domain)**: `models.py` 定义核心实体（Player, Room, Enemy, Item）；`services/` 包含纯业务逻辑（如 CombatService）。
3.  **基础设施层 (Infrastructure)**: `snapshot.py` 负责状态快照转换；`infrastructure/json_save_repository.py` 负责持久化。

## 目录结构说明
- `game/`: 源代码根目录。
  - `services/`: 领域服务，专注于复杂计算。
  - `infrastructure/`: 外部依赖实现（文件 IO、数据库等）。
- `tests/`: 单元测试目录，包含 Mock 测试和集成测试。

## 核心模块职责
- `GameEngine`: 状态机中心，协调移动、拾取、战斗流程，管理内存中的房间和玩家。
- `CombatService`: 纯逻辑服务，不持有状态，仅计算伤害和升级。
- `CommandHandler`: 输入路由器，负责字符串到方法名的映射及参数正则提取。

## 编码规范约束
- **输入容错**: 命令解析需支持 `cmd<arg>` 和 `cmd arg` 格式（由 `CommandHandler` 处理）。
- **Mock 优先**: 编写 `engine.py` 或 `commands.py` 的测试时，必须 Mock 其依赖的领域模型或子服务。
- **不可变快照**: 存档逻辑必须通过 `GameSnapshot` 中转，禁止直接序列化领域模型。

## 禁止操作清单
- ❌ **禁止** 在 `CombatService` 中直接修改 `GameEngine` 的属性（应通过返回 `CombatResult`）。
- ❌ **禁止** 在 `models.py` 中编写任何文件 IO 或网络请求代码。
- ❌ **禁止** 在测试中使用 `time.sleep()`，应使用模拟时钟或立即执行。
- ❌ **禁止** 直接在 `main.py` 中编写业务逻辑，它仅作为程序入口。
