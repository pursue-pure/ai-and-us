# 产品待办列表（Product Backlog）

> 文档版本：Sprint 3 规划版  
> 更新日期：2026 年 4 月 8 日  
> 更新依据：Sprint 2 Scrum 回顾报告、详细设计说明书（DDS）、OOA 建模与重构报告、当前代码库实际状态  
> 说明：Sprint 2 完成了架构审查、OOA 建模、DFD 分析与重构方案设计，但重构代码**尚未落地**。当前 `game/` 目录仍为 Sprint 1 的原始高耦合结构。本 Backlog 以"设计已确认、代码未实现"为基准，梳理全部遗留任务并排定优先级，作为 Sprint 3 规划的直接输入。

---

## 一、遗留任务总览

| 编号 | 任务名称 | 来源 | 优先级 | 负责人 | 预计完成时间 |
|------|----------|------|--------|--------|--------------|
| PB-01 | 提取 `CombatService`，拆解 `attack_enemy()` 上帝方法 | Sprint 2 DDS §3.2 | 高 | 曹睿杰 | Sprint 3 |
| PB-02 | 修复 US-006：存档读档未完整恢复房间状态（敌人 / 物品） | 用户故事池 US-006 | 高 | 张津毓 | Sprint 3 |
| PB-03 | 提取 `JsonSaveRepository`，解耦持久化与引擎 | Sprint 2 DDS §3.5 | 高 | 张津毓 | Sprint 3 |
| PB-04 | 提取 `CheckpointService`，解耦复活与检查点逻辑 | Sprint 2 DDS §3.4 | 高 | 曹睿杰 | Sprint 3 |
| PB-05 | 补全核心服务层单元测试（战斗 / 复活 / 存读档分支） | Sprint 2 DDS §6.3 | 高 | 张津毓 | Sprint 3 |
| PB-06 | 提取 `InventoryService`，消除 `item_type` 多处重复分支 | Sprint 2 DDS §3.3 | 中 | 曹睿杰 | Sprint 3 |
| PB-07 | 引入 `LegacyCommandAdapter`，隔离命令层与新服务层 | Sprint 2 DDS §2.1 | 中 | 王鹏 | Sprint 3 |
| PB-08 | 引入 `WorldBuilder` 工厂，统一世界初始化与读档重建 | Sprint 2 DDS §3.6 | 中 | 王鹏 | Sprint 3 |
| PB-09 | 建立 `GameSnapshot` 统一快照模型 | Sprint 2 回顾报告 §5 | 中 | 张津毓 | Sprint 3 |
| PB-10 | 引入策略模式：`CombatResolutionStrategy` / `ItemEffectStrategy` | Sprint 2 DDS §2.3 | 低 | 曹睿杰 | 后续迭代 |
| PB-11 | 引入 `GameContext` 单例，统一运行时上下文与仓储注册 | Sprint 2 DDS §2.3 | 低 | 王鹏 | 后续迭代 |
| PB-12 | CI 集成 McCabe 复杂度门禁（单方法阈值 ≤ 7） | Sprint 2 回顾报告 §5 | 低 | 王鹏 | 后续迭代 |

---

## 二、高优先级任务（必须在 Sprint 3 完成）

### PB-01 提取 `CombatService`，拆解 `attack_enemy()` 上帝方法

**任务描述**  
当前 `game/engine.py` 中的 `GameEngine.attack_enemy()` 方法同时承担：前置校验（房间是否有存活敌人）、玩家攻击力计算、敌人扣血、敌人反击、经验结算、升级判定、BOSS 胜利判定、死亡状态记录、死亡时间写入、CLI 文本拼装，共 10 项职责，McCabe 圈复杂度超标。  
需按 DDS §3.2 设计，新建 `game/services/combat_service.py`，将上述职责拆分为：
- `attack(player, room)` — 战斗主入口，返回结构化 `CombatResult`
- `_apply_player_attack(player, enemy)` — 计算并应用玩家伤害
- `_resolve_victory(player, room, enemy)` — 结算经验、升级与 BOSS 胜利
- `_resolve_counter_attack(player, enemy)` — 处理敌人反击和玩家死亡

`GameEngine.attack_enemy()` 重构为仅调用 `CombatService.attack()` 并格式化输出的薄包装。

**优先级判定依据**  
`attack_enemy()` 是当前复杂度最高的方法，任何战斗相关 bug 修复或功能扩展都必须改动该方法，风险最高；且 PB-04（CheckpointService）依赖本任务完成后才能干净解耦死亡记录逻辑。

**验收标准**
- [ ] `CombatService` 独立可实例化，不直接依赖 `GameEngine`
- [ ] `GameEngine.attack_enemy()` 圈复杂度降至 ≤ 5
- [ ] 原有 21 个测试用例全部通过（无回归）
- [ ] 新增战斗分支测试：无敌人、普通命中、升级触发、击败 BOSS、玩家死亡

**优先级：** 高  
**负责人：** 曹睿杰  
**预计完成时间：** Sprint 3

---

### PB-02 修复 US-006：存档读档未完整恢复房间状态（敌人 / 物品）

**任务描述**  
当前 `GameEngine.load_game()` 在恢复房间状态时，仅恢复了 `has_looked` 标志，未恢复：
1. 敌人的存活状态（`enemy.hp`）——读档后已被击败的敌人会复活
2. 房间物品列表——读档后已被拾取的物品会重新出现

需在存档 JSON 的 `rooms` 节点中补充 `enemy_hp` 和 `items` 字段，并在 `load_game()` 中完整恢复这两项状态。此修复可先在现有 `engine.py` 中完成，后续由 PB-03 迁移至 `JsonSaveRepository`。

**优先级判定依据**  
这是 Sprint 1 遗留的已知功能缺陷（US-006 验收标准未全部通过），直接影响玩家存读档体验的正确性，属于功能性 bug，必须在下一 Sprint 修复。

**验收标准**
- [ ] 击败哥布林后存档，读档后哥布林保持死亡状态（`hp == 0`）
- [ ] 拾取铁剑后存档，读档后宝藏室物品列表中不再出现铁剑
- [ ] 检查点元数据（`checkpoint_room_id`、`checkpoint_time`）读档后与存档一致
- [ ] 新增测试用例覆盖上述三类场景

**优先级：** 高  
**负责人：** 张津毓  
**预计完成时间：** Sprint 3

---

### PB-03 提取 `JsonSaveRepository`，解耦持久化与引擎

**任务描述**  
当前 `GameEngine.save_game()` 和 `load_game()` 将文件读写、JSON 序列化、对象重建、检查点回填、异常处理全部混写在引擎中，导致持久化格式变更必须修改引擎核心类。  
需按 DDS §3.5 设计，新建 `game/infrastructure/json_save_repository.py`，实现：
- `save(snapshot: GameSnapshot, filename: str)` — 序列化并写入文件
- `load(filename: str) -> GameSnapshot` — 读取文件并反序列化为快照对象
- 文件不存在、JSON 结构损坏时抛出明确的 `SaveLoadError` 领域异常

`GameEngine.save_game()` / `load_game()` 重构为调用仓储并处理异常的薄包装。

**优先级判定依据**  
PB-02 的 bug 修复需要扩展存档结构，若不同步解耦持久化层，修复代码仍会继续堆积在 `GameEngine` 中，形成新的耦合。两项任务在 Sprint 3 中应配合推进。

**验收标准**
- [ ] `JsonSaveRepository` 可独立实例化和测试，不依赖 `GameEngine`
- [ ] `GameEngine` 中不再包含任何 `json.dump` / `json.load` 直接调用
- [ ] 合法存档、缺失文件、结构损坏三类场景均有对应测试

**优先级：** 高  
**负责人：** 张津毓  
**预计完成时间：** Sprint 3

---

### PB-04 提取 `CheckpointService`，解耦复活与检查点逻辑

**任务描述**  
当前检查点状态（`checkpoint_room_id`、`checkpoint_time`、`last_death_time`、`last_respawn_time`）直接挂在 `GameEngine` 实例上，`respawn()` 方法与 `attack_enemy()` 中的死亡分支共同维护这些字段，形成跨方法的隐式状态依赖。  
需按 DDS §3.4 设计，新建 `game/services/checkpoint_service.py`，实现：
- `update_checkpoint(room_id)` — 更新检查点位置与时间
- `record_death()` — 记录死亡时间
- `respawn(player, rooms) -> RespawnResult` — 执行复活并返回结构化结果

**优先级判定依据**  
PB-01 拆解 `CombatService` 时，死亡记录逻辑必须有明确的归属类，否则 `CombatService` 仍需直接操作 `GameEngine` 的字段，解耦不彻底。

**验收标准**
- [ ] `CheckpointService` 独立可实例化，不直接依赖 `GameEngine`
- [ ] `GameEngine` 中不再直接操作 `checkpoint_room_id` 等字段
- [ ] 成功复活、无有效检查点两类分支均有测试覆盖

**优先级：** 高  
**负责人：** 曹睿杰  
**预计完成时间：** Sprint 3

---

### PB-05 补全核心服务层单元测试

**任务描述**  
PB-01 至 PB-04 完成后，需同步补全对应测试，确保重构不引入回归。需覆盖以下分支（来自 DDS §6.3）：

| 测试目标 | 需覆盖的分支 |
|----------|-------------|
| `CombatService.attack()` | 无敌人、普通命中、升级触发、击败 BOSS、玩家死亡 |
| `InventoryService.take_item()` | 未执行 `look`、成功拾取、物品不存在 |
| `CheckpointService.respawn()` | 成功复活回检查点、无有效检查点时的降级处理 |
| `JsonSaveRepository.load()` | 合法存档、文件不存在、JSON 结构损坏 |

**优先级判定依据**  
无测试保护的重构等于盲目改动。Sprint 2 回顾报告明确指出"通过测试守住 Sprint 1 已实现玩法"是本次重构的底线要求。

**验收标准**
- [ ] 新增测试用例 ≥ 15 个，覆盖上表所有分支
- [ ] `pytest tests/ -v` 全部通过，无跳过项
- [ ] 原有 21 个测试用例无回归

**优先级：** 高  
**负责人：** 张津毓  
**预计完成时间：** Sprint 3

---

## 三、中优先级任务（可根据 Sprint 3 资源调整）

### PB-06 提取 `InventoryService`，消除 `item_type` 多处重复分支

**任务描述**  
`Player.use_item()`、`GameEngine.take_item()`、`GameEngine.show_inventory()` 三处均通过 `item_type == "potion"` / `"weapon"` 做条件分支判断物品效果，同一逻辑分散在三个类中，新增物品类型时需同步修改三处。  
需按 DDS §3.3 设计，新建 `game/services/inventory_service.py`，将物品效果判断收敛到 `InventoryService`，并为后续引入 `ItemEffectStrategy`（PB-10）预留扩展点。

**优先级判定依据**  
当前物品系统功能完整，无已知 bug，但扩展成本高。可在 PB-01 至 PB-05 完成后推进，不阻塞核心重构路径。

**验收标准**
- [ ] `GameEngine` 中不再出现 `item_type` 条件分支
- [ ] `Player.use_item()` 中的效果逻辑迁移至 `InventoryService`
- [ ] 拾取、使用、背包展示三类场景测试通过

**优先级：** 中  
**负责人：** 曹睿杰  
**预计完成时间：** Sprint 3

---

### PB-07 引入 `LegacyCommandAdapter`，隔离命令层与新服务层

**任务描述**  
当前 `CommandHandler` 直接调用 `GameEngine` 的具体方法名（如 `attack_enemy()`、`take_item()`），PB-01 至 PB-06 完成后，`GameEngine` 的方法签名可能发生变化，需在命令层与引擎层之间增加适配器，保持 CLI 命令入口稳定。  
新建 `game/adapters/legacy_command_adapter.py`，将 `CommandHandler` 的调用转发至新服务层，同时兼容现有测试中对命令处理器的直接调用。

**优先级判定依据**  
适配器是渐进式重构的保护层，在服务层稳定后再引入更合适，避免过早抽象。

**验收标准**
- [ ] `CommandHandler` 不再直接引用 `GameEngine` 的业务方法
- [ ] 所有命令（`attack`、`save`、`load`、`respawn` 等）通过适配器后行为不变
- [ ] 原有命令处理器测试全部通过

**优先级：** 中  
**负责人：** 王鹏  
**预计完成时间：** Sprint 3

---

### PB-08 引入 `WorldBuilder` 工厂，统一世界初始化与读档重建

**任务描述**  
当前 `game/main.py` 中的 `create_demo_world()` 函数直接硬编码所有房间、物品、敌人的构造逻辑；`load_game()` 中也有独立的对象重建逻辑，两套创建规则不一致，导致"正常开局"与"读档回档"可能产生状态差异。  
需按 DDS §3.6 设计，新建 `game/infrastructure/world_builder.py`，将两处创建逻辑统一收口，`load_game()` 的对象重建改为调用 `WorldBuilder`。

**优先级判定依据**  
依赖 PB-03（`JsonSaveRepository`）完成后推进，两者共同消除读档状态不一致问题。

**验收标准**
- [ ] `main.py` 中的世界构建逻辑迁移至 `WorldBuilder`
- [ ] 读档重建与正常开局使用同一套工厂方法
- [ ] 新增测试验证两种路径下初始房间状态一致

**优先级：** 中  
**负责人：** 王鹏  
**预计完成时间：** Sprint 3

---

### PB-09 建立 `GameSnapshot` 统一快照模型

**任务描述**  
当前存档 JSON 结构与运行态对象之间存在隐式映射（字段名硬编码在 `save_game()` / `load_game()` 中），字段变更时容易遗漏。  
需新建 `game/models/snapshot.py`，定义 `GameSnapshot`、`PlayerSnapshot`、`RoomSnapshot` 三个数据类，作为运行态与持久化之间的统一中间层，`JsonSaveRepository` 的序列化 / 反序列化均基于快照模型操作。

**优先级判定依据**  
依赖 PB-03 完成后推进，是存档系统长期可维护性的基础，但不阻塞 PB-02 的 bug 修复。

**验收标准**
- [ ] `GameSnapshot` / `PlayerSnapshot` / `RoomSnapshot` 定义完整，字段与当前存档结构对齐
- [ ] `JsonSaveRepository` 的序列化 / 反序列化基于快照模型，不再直接操作运行态对象字段
- [ ] 快照模型有对应的序列化 / 反序列化单元测试

**优先级：** 中  
**负责人：** 张津毓  
**预计完成时间：** Sprint 3

---

## 四、低优先级任务（后续迭代逐步完成）

### PB-10 引入策略模式：`CombatResolutionStrategy` / `ItemEffectStrategy`

**任务描述**  
在 PB-01 和 PB-06 完成后，将战斗结果判定（普通命中 / 暴击 / 闪避）和物品效果（药水治疗 / 武器加成 / 工具效果）从硬编码分支迁移为可替换的策略对象，为后续扩展新敌人行为、新物品类型提供扩展点，无需修改现有服务类。

**优先级判定依据**  
当前物品类型和战斗规则固定，策略模式的收益在功能扩展时才会显现，MVP 阶段不紧迫。

**验收标准**
- [ ] `CombatService` 通过策略接口调用战斗结果判定，不含硬编码分支
- [ ] 新增一种物品类型只需新增策略类，不修改 `InventoryService`

**优先级：** 低  
**负责人：** 曹睿杰  
**预计完成时间：** 后续迭代

---

### PB-11 引入 `GameContext` 单例，统一运行时上下文与仓储注册

**任务描述**  
在 PB-03 至 PB-08 完成后，将全局唯一的运行上下文（检查点配置、仓储实例）统一托管到 `GameContext`，避免多个服务各自持有一份状态副本。注意：仅在"全局唯一对象"场景使用单例，不将业务服务设计为单例。

**优先级判定依据**  
依赖服务层稳定后才有意义，过早引入会制造新的全局耦合。

**验收标准**
- [ ] `GameContext` 在同一轮游戏内只有一个实例
- [ ] 各服务通过 `GameContext` 获取仓储引用，不各自创建

**优先级：** 低  
**负责人：** 王鹏  
**预计完成时间：** 后续迭代

---

### PB-12 CI 集成 McCabe 复杂度门禁

**任务描述**  
在 CI 流程中加入静态复杂度检查（推荐使用 `radon` 或 `flake8-cognitive-complexity`），将单方法 McCabe 圈复杂度阈值设为 7，超过阈值时构建失败并要求拆分或补充设计说明。

**优先级判定依据**  
属于工程质量保障措施，在重构完成后引入效果最佳，避免在重构过渡期频繁触发门禁。

**验收标准**
- [ ] CI 配置文件中包含复杂度检查步骤
- [ ] 当前所有方法复杂度 ≤ 7（重构完成后）
- [ ] 超标时 CI 输出明确的方法名与复杂度数值

**优先级：** 低  
**负责人：** 王鹏  
**预计完成时间：** 后续迭代

---

## 五、优先级判定依据汇总

| 优先级 | 判定标准 | 对应任务 |
|--------|----------|----------|
| **高** | 存在已知功能 bug（US-006）；或是其他任务的前置依赖；或是当前复杂度最高、风险最大的方法 | PB-01 至 PB-05 |
| **中** | 功能完整但扩展成本高；或依赖高优先级任务完成后才能干净推进；不阻塞核心玩法 | PB-06 至 PB-09 |
| **低** | 属于架构质量提升或工程规范建设；当前无功能缺陷；收益在后续功能扩展时才显现 | PB-10 至 PB-12 |

---

## 六、Sprint 3 建议启动顺序

```
第 1 步：PB-02（修复存档 bug）+ PB-03（JsonSaveRepository）并行推进
第 2 步：PB-01（CombatService）+ PB-04（CheckpointService）并行推进
第 3 步：PB-05（补全测试）— 在上述服务稳定后集中补测
第 4 步：PB-06（InventoryService）+ PB-07（LegacyCommandAdapter）
第 5 步：PB-08（WorldBuilder）+ PB-09（GameSnapshot）
第 6 步（视资源）：PB-10 至 PB-12
```

---

**Product Backlog 更新结论**  
Sprint 2 完成了架构审查与重构方案设计，Sprint 3 的核心任务是将已确认的设计方案落地为可运行代码，同时修复 US-006 存档恢复缺陷，并以测试覆盖保障重构安全性。
