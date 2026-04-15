# Sprint 2 详细设计说明书（DDS）

> 文档定位：本说明书面向 Sprint 2 中“高耦合遗留代码重构”的目标设计与阶段性成果归档，重点描述核心控制类、关键算法流程及跨类调用接口规范，供团队后续开发、维护与测试对照使用。  
> 适用范围：`ai-and-us` 控制台 MUD 游戏在 Sprint 2 的目标重构架构（含部分已落地实现）。  
> 关联文档：`Sprint2_OOA建模与重构报告.md`、`Sprint2_Scrum回顾报告.md`

## 1. 文档基本信息

### 1.1 文档目标

- 将 Sprint 2 中从高耦合遗留代码中提取出的核心控制类进行规范化归档
- 统一跨类调用方法签名，减少后续迭代中的接口漂移
- 为关键控制算法提供结构化图示，支撑实现、评审与测试

### 1.2 适配的重构目标

本次 DDS 对应的重构目标如下：

1. 将原 `GameEngine` 的多职责结构拆分为轻量协调层与多个业务服务
2. 将战斗、背包、检查点、存档从引擎中解耦
3. 将遗留的条件分支逻辑迁移为工厂、适配器、策略等模式协作
4. 保持现有命令行交互入口不变，降低对上层调用方的影响

## 2. 重构后架构概览

### 2.1 架构分层

重构后的详细设计采用四层结构：

- 表现层：`LegacyCommandAdapter`
- 协调层：`GameEngine`
- 业务控制层：`CombatService`、`InventoryService`、`CheckpointService`
- 基础设施层：`WorldBuilder`、`JsonSaveRepository`

### 2.1.1 当前落地状态（截至 2026-04-15）

- 已落地：`GameEngine`（部分薄化）、`CombatService`、`CombatResult`、`JsonSaveRepository`、`GameSnapshot`、`PlayerSnapshot`、`RoomSnapshot`、`EnemySnapshot`、命令解析兼容能力（由 `CommandHandler` 提供）
- 待落地：`InventoryService`、`CheckpointService`、`WorldBuilder`、`LegacyCommandAdapter`
- 说明：本 DDS 的其余章节保留目标态接口定义，作为 Sprint 3 的实现基线。

### 2.2 核心协作关系

```text
Console Input
    ↓
LegacyCommandAdapter
    ↓
GameEngine (Facade)
    ├── Movement/Room coordination
    ├── CombatService
    ├── InventoryService
    ├── CheckpointService
    ├── JsonSaveRepository
    └── WorldBuilder
```

### 2.3 设计模式落位

| 设计模式 | 对应类 | 设计目的 |
|----------|--------|----------|
| 工厂模式 | `WorldBuilder` | 统一房间、物品、敌人和玩家的创建逻辑 |
| 适配器模式 | `LegacyCommandAdapter` | 保持旧命令接口兼容，适配新服务层 |
| 单例模式 | `GameContext` 或 `RepositoryRegistry` | 统一运行时上下文和仓储配置 |
| 策略模式 | `CombatResolutionStrategy`、`ItemEffectStrategy` | 替代分支驱动的行为判断 |
| 外观模式 | `GameEngine` | 对外提供统一入口，对内协调多个服务 |

## 3. 核心控制类详细设计（目标态）

> 说明：本节只聚焦本次重构提取出的核心控制类，不重复展开实体类 `Player`、`Room`、`Item`、`Enemy` 的基础字段。

### 3.1 GameEngine

#### 3.1.1 类职责

`GameEngine` 作为轻量级外观控制类，负责统一接收命令层请求，协调移动、战斗、背包、检查点和持久化服务，不再直接承担复杂业务分支与对象重建逻辑。

#### 3.1.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `rooms` | `dict[str, Room]` | 当前世界中的房间集合 |
| `player` | `Player` | 当前玩家对象 |
| `running` | `bool` | 游戏主循环状态 |
| `game_won` | `bool` | 是否达成胜利状态 |
| `combat_service` | `CombatService` | 战斗控制服务 |
| `inventory_service` | `InventoryService` | 物品控制服务 |
| `checkpoint_service` | `CheckpointService` | 检查点与复活控制服务 |
| `repository` | `JsonSaveRepository` | 存读档仓储 |
| `world_builder` | `WorldBuilder` | 世界构建工厂 |

#### 3.1.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `bootstrap_world()` | 初始化默认世界并创建玩家 |
| `move_player(direction)` | 协调移动逻辑并返回文本结果 |
| `attack_enemy()` | 委托 `CombatService` 执行战斗并格式化输出 |
| `take_item(item_name)` | 委托 `InventoryService` 执行拾取 |
| `use_item(item_name)` | 委托 `InventoryService` 执行使用 |
| `respawn()` | 委托 `CheckpointService` 执行复活 |
| `save_game(filename)` | 构造快照并交给仓储持久化 |
| `load_game(filename)` | 从仓储加载快照并恢复游戏上下文 |

### 3.2 CombatService

#### 3.2.1 类职责

`CombatService` 负责战斗流程的控制与状态结算，包括攻击前置校验、玩家伤害计算、敌人反击、经验结算、升级判定、BOSS 胜利判定以及死亡结果封装。

#### 3.2.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `resolution_strategy` | `CombatResolutionStrategy` | 战斗结果判定策略 |
| `checkpoint_service` | `CheckpointService` | 玩家死亡时用于记录检查点与死亡时间 |
| `result_formatter` | `CombatResultFormatter` | 将结构化结果转换为 CLI 文本 |

#### 3.2.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `attack(player, room)` | 战斗主入口，返回结构化战斗结果 |
| `_apply_player_attack(player, enemy)` | 计算并应用玩家伤害 |
| `_resolve_victory(player, room, enemy)` | 结算经验、升级与 BOSS 胜利 |
| `_resolve_counter_attack(player, enemy)` | 处理敌人反击和玩家死亡 |

### 3.3 InventoryService

#### 3.3.1 类职责

`InventoryService` 负责房间物品发现、物品拾取、背包展示及物品使用。物品效果本身由 `ItemEffectStrategy` 实现，`InventoryService` 只负责控制流程与结果装配。

#### 3.3.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `effect_registry` | `dict[str, ItemEffectStrategy]` | 物品效果策略注册表 |
| `result_formatter` | `InventoryResultFormatter` | 统一格式化拾取/使用结果 |

#### 3.3.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `take_item(player, room, item_name)` | 控制拾取流程 |
| `use_item(player, item_name)` | 控制使用流程 |
| `show_inventory(player)` | 生成背包展示结果 |
| `_resolve_strategy(item)` | 根据物品类型返回对应策略实现 |

### 3.4 CheckpointService

#### 3.4.1 类职责

`CheckpointService` 负责检查点记录、死亡时间记录、复活位置解析与复活结果输出，是玩家生命周期控制的唯一状态源。

#### 3.4.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `checkpoint_room_id` | `str` | 当前有效检查点房间 ID |
| `checkpoint_time` | `str` | 检查点记录时间 |
| `last_death_time` | `str` | 最近一次死亡时间 |
| `last_respawn_time` | `str` | 最近一次复活时间 |

#### 3.4.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `update(room_id)` | 更新检查点房间和记录时间 |
| `mark_death()` | 记录死亡时间 |
| `resolve_checkpoint(rooms, player)` | 解析当前可用检查点 |
| `respawn(player, rooms)` | 执行玩家复活并返回结果对象 |

### 3.5 JsonSaveRepository

#### 3.5.1 类职责

`JsonSaveRepository` 负责将运行态对象映射为可持久化快照，并执行 JSON 写入/读取。该类不承担战斗、背包、命令解析等业务逻辑。

#### 3.5.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `encoder` | `SnapshotEncoder` | 领域对象到快照对象的转换器 |
| `decoder` | `SnapshotDecoder` | 快照对象到领域对象的转换器 |
| `default_encoding` | `str` | 默认字符编码，固定为 `utf-8` |

#### 3.5.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `save(filename, snapshot)` | 将快照持久化到 JSON 文件 |
| `load(filename)` | 从 JSON 文件恢复快照 |

### 3.6 WorldBuilder

#### 3.6.1 类职责

`WorldBuilder` 负责创建默认游戏世界和恢复世界对象，统一对象初始化规则，消除 `main.py` 与 `load_game()` 中对象构造逻辑重复。

#### 3.6.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `item_factory` | `ItemFactory` | 物品工厂 |
| `enemy_factory` | `EnemyFactory` | 敌人工厂 |
| `room_factory` | `RoomFactory` | 房间工厂 |

#### 3.6.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `build_default_world()` | 创建默认房间、敌人、物品与玩家起点 |
| `restore_rooms(room_snapshots)` | 根据存档快照恢复房间状态 |
| `restore_player(player_snapshot)` | 根据存档快照恢复玩家状态 |

### 3.7 LegacyCommandAdapter

#### 3.7.1 类职责

`LegacyCommandAdapter` 负责将控制台原始文本命令适配为重构后引擎可识别的调用，保证 `help`、`attack`、`save`、`load`、`take<物品>` 等旧接口行为不变。

#### 3.7.2 关键属性

| 属性名 | 类型 | 说明 |
|--------|------|------|
| `engine` | `GameEngine` | 被适配的核心控制器 |
| `command_map` | `dict[str, Callable]` | 命令关键字到处理函数的映射 |

#### 3.7.3 核心方法

| 方法名 | 职责说明 |
|--------|----------|
| `handle(user_input)` | 命令总入口 |
| `parse(user_input)` | 解析紧凑命令、尖括号输入与方向命令 |
| `dispatch(command, args)` | 根据命令分派到引擎能力 |

## 4. 跨类调用方法签名规范（目标态）

### 4.1 GameEngine 对外方法签名

#### 4.1.1 `bootstrap_world`

- 方法名：`bootstrap_world`
- 签名：`bootstrap_world(player_name: str = "冒险者") -> None`
- 参数说明：
  - `player_name: str`，玩家初始名称
- 返回值：`None`
- 异常：
  - `ValueError`：世界初始化失败或起始房间不存在

#### 4.1.2 `move_player`

- 方法名：`move_player`
- 签名：`move_player(direction: str) -> str`
- 参数说明：
  - `direction: str`，移动方向，例如 `north`、`south`
- 返回值：`str`，CLI 可直接展示的房间移动结果
- 异常：
  - 不主动抛出业务异常，统一由返回文本表达失败原因

#### 4.1.3 `attack_enemy`

- 方法名：`attack_enemy`
- 签名：`attack_enemy() -> str`
- 参数说明：无
- 返回值：`str`，战斗结果文本
- 异常：
  - `RuntimeError`：战斗服务未注入

#### 4.1.4 `save_game`

- 方法名：`save_game`
- 签名：`save_game(filename: str) -> str`
- 参数说明：
  - `filename: str`，目标存档文件名
- 返回值：`str`，保存结果文本
- 异常：
  - `OSError`：文件无法写入
  - `ValueError`：快照编码失败

#### 4.1.5 `load_game`

- 方法名：`load_game`
- 签名：`load_game(filename: str) -> str`
- 参数说明：
  - `filename: str`，目标存档文件名
- 返回值：`str`，加载结果文本
- 异常：
  - `FileNotFoundError`：存档文件不存在
  - `ValueError`：存档结构不合法

### 4.2 GameEngine 与 CombatService 调用签名

- 方法名：`attack`
- 签名：`attack(player: Player, room: Room) -> CombatResult`
- 参数说明：
  - `player: Player`，当前玩家对象
  - `room: Room`，当前房间对象
- 返回值：`CombatResult`
- 异常：
  - `GameStateError`：玩家或房间状态非法

`CombatResult` 结构说明：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `status` | `str` | `no_enemy / hit / victory / dead / invalid` |
| `player_damage` | `int` | 玩家造成伤害 |
| `enemy_damage` | `int` | 敌人反击伤害 |
| `enemy_defeated` | `bool` | 敌人是否被击败 |
| `player_dead` | `bool` | 玩家是否死亡 |
| `leveled_up` | `bool` | 是否升级 |
| `game_won` | `bool` | 是否触发 BOSS 胜利 |
| `message` | `str` | 默认结果消息 |

### 4.3 GameEngine 与 InventoryService 调用签名

#### 4.3.1 `take_item`

- 方法名：`take_item`
- 签名：`take_item(player: Player, room: Room, item_name: str) -> InventoryActionResult`
- 参数说明：
  - `player: Player`，当前玩家对象
  - `room: Room`，当前房间对象
  - `item_name: str`，目标物品名称
- 返回值：`InventoryActionResult`
- 异常：
  - `GameStateError`：玩家状态非法

#### 4.3.2 `use_item`

- 方法名：`use_item`
- 签名：`use_item(player: Player, item_name: str) -> InventoryActionResult`
- 参数说明：
  - `player: Player`，当前玩家对象
  - `item_name: str`，目标物品名称
- 返回值：`InventoryActionResult`
- 异常：
  - `GameStateError`：玩家状态非法

`InventoryActionResult` 结构说明：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `status` | `str` | `taken / used / not_found / blocked / invalid` |
| `item_name` | `str` | 目标物品名称 |
| `effect_value` | `int` | 物品生效数值 |
| `message` | `str` | 默认结果消息 |

### 4.4 GameEngine 与 CheckpointService 调用签名

#### 4.4.1 `update`

- 方法名：`update`
- 签名：`update(room_id: str, timestamp: str | None = None) -> None`
- 参数说明：
  - `room_id: str`，房间 ID
  - `timestamp: str | None`，可选时间戳，不传则使用当前时间
- 返回值：`None`
- 异常：
  - `ValueError`：房间 ID 非法

#### 4.4.2 `respawn`

- 方法名：`respawn`
- 签名：`respawn(player: Player, rooms: dict[str, Room]) -> RespawnResult`
- 参数说明：
  - `player: Player`，当前玩家
  - `rooms: dict[str, Room]`，房间集合
- 返回值：`RespawnResult`
- 异常：
  - `GameStateError`：没有可用检查点

`RespawnResult` 结构说明：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `success` | `bool` | 是否复活成功 |
| `room_id` | `str` | 复活房间 ID |
| `restored_hp` | `int` | 恢复后的 HP |
| `checkpoint_time` | `str` | 检查点记录时间 |
| `message` | `str` | 默认结果消息 |

### 4.5 GameEngine 与 JsonSaveRepository 调用签名

#### 4.5.1 `save`

- 方法名：`save`
- 签名：`save(filename: str, snapshot: GameSnapshot) -> None`
- 参数说明：
  - `filename: str`，存档文件名
  - `snapshot: GameSnapshot`，当前游戏快照
- 返回值：`None`
- 异常：
  - `OSError`：文件写入失败
  - `ValueError`：快照对象序列化失败

#### 4.5.2 `load`

- 方法名：`load`
- 签名：`load(filename: str) -> GameSnapshot`
- 参数说明：
  - `filename: str`，存档文件名
- 返回值：`GameSnapshot`
- 异常：
  - `FileNotFoundError`：目标文件不存在
  - `ValueError`：JSON 结构不合法

### 4.6 WorldBuilder 构建签名

#### 4.6.1 `build_default_world`

- 方法名：`build_default_world`
- 签名：`build_default_world(player_name: str) -> tuple[dict[str, Room], Player]`
- 参数说明：
  - `player_name: str`，玩家名称
- 返回值：
  - `tuple[dict[str, Room], Player]`，房间集合与玩家对象
- 异常：
  - `ValueError`：默认地图配置缺失

#### 4.6.2 `restore_rooms`

- 方法名：`restore_rooms`
- 签名：`restore_rooms(room_snapshots: list[RoomSnapshot]) -> dict[str, Room]`
- 参数说明：
  - `room_snapshots: list[RoomSnapshot]`，房间快照集合
- 返回值：
  - `dict[str, Room]`，恢复后的房间字典
- 异常：
  - `ValueError`：快照字段缺失或状态非法

### 4.7 LegacyCommandAdapter 调用签名

#### 4.7.1 `handle`

- 方法名：`handle`
- 签名：`handle(user_input: str) -> str`
- 参数说明：
  - `user_input: str`，用户输入的原始命令
- 返回值：`str`，命令执行结果文本
- 异常：
  - 不直接抛出解析异常，统一返回可读提示文本

#### 4.7.2 `parse`

- 方法名：`parse`
- 签名：`parse(user_input: str) -> tuple[str, list[str]]`
- 参数说明：
  - `user_input: str`，原始命令文本
- 返回值：
  - `tuple[str, list[str]]`，命令字与参数列表
- 异常：
  - `ValueError`：命令语法完全非法

## 5. 关键算法 N-S 盒图（目标态）

> 说明：本节采用 N-S 盒图归档关键控制算法，图中使用“顺序 / 条件 / 循环”描述与代码流程一一对应。

### 5.1 CombatService.attack() N-S 盒图

```text
┌──────────────────────────────────────────────────────────────┐
│ CombatService.attack(player: Player, room: Room)            │
├──────────────────────────────────────────────────────────────┤
│ 1. 校验 player 是否存在且处于可战斗状态                     │
├──────────────────────────────────────────────────────────────┤
│ IF player 为空 或 player.is_alive = False                   │
│    RETURN CombatResult(status="invalid")                    │
│ ELSE                                                        │
│    2. 读取 room.enemy                                        │
├──────────────────────────────────────────────────────────────┤
│ IF enemy 不存在 或 enemy.is_alive() = False                 │
│    RETURN CombatResult(status="no_enemy")                   │
│ ELSE                                                        │
│    3. 计算玩家攻击力                                         │
│    4. enemy.take_damage(player_damage)                      │
├──────────────────────────────────────────────────────────────┤
│ IF enemy 被击败                                             │
│    5. 结算经验值、升级状态、BOSS 胜利状态                    │
│    6. 清理当前房间敌人引用                                   │
│    RETURN CombatResult(status="victory")                    │
│ ELSE                                                        │
│    7. 执行敌人反击                                           │
│    8. player.take_damage(enemy_damage)                      │
├──────────────────────────────────────────────────────────────┤
│ IF player 死亡                                              │
│    9. checkpoint_service.mark_death()                       │
│    RETURN CombatResult(status="dead")                       │
│ ELSE                                                        │
│    RETURN CombatResult(status="hit")                        │
└──────────────────────────────────────────────────────────────┘
```

#### 5.1.1 算法说明

- 该算法没有显式循环，核心控制点在三次条件判断：
  - 是否可战斗
  - 是否存在可攻击敌人
  - 攻击后进入胜利分支还是反击分支
- 与原始 `GameEngine.attack_enemy()` 相比，升级、胜利提示、死亡记录均不再夹杂在同一长方法里，而是通过结果对象和服务协作完成

### 5.2 JsonSaveRepository.load() N-S 盒图

```text
┌──────────────────────────────────────────────────────────────┐
│ JsonSaveRepository.load(filename: str)                      │
├──────────────────────────────────────────────────────────────┤
│ 1. 打开并读取 JSON 文件                                      │
├──────────────────────────────────────────────────────────────┤
│ IF 文件不存在                                                │
│    RAISE FileNotFoundError                                  │
│ ELSE                                                        │
│    2. 将 JSON 反序列化为 snapshot 原始字典                   │
├──────────────────────────────────────────────────────────────┤
│ IF snapshot 结构缺失关键字段                                 │
│    RAISE ValueError                                         │
│ ELSE                                                        │
│    3. decoder.decode(snapshot_dict)                         │
├──────────────────────────────────────────────────────────────┤
│ FOR each player_item_snapshot in player_snapshot.inventory   │
│    4. 使用 ItemFactory 重建玩家背包物品                      │
├──────────────────────────────────────────────────────────────┤
│ FOR each room_snapshot in room_snapshots                     │
│    5. 使用 WorldBuilder.restore_rooms() 恢复房间状态         │
├──────────────────────────────────────────────────────────────┤
│ 6. 恢复 checkpoint / death / respawn 元数据                 │
│ 7. RETURN GameSnapshot                                      │
└──────────────────────────────────────────────────────────────┘
```

#### 5.2.1 算法说明

- 该算法包含两段显式循环：
  - 玩家背包物品恢复循环
  - 房间快照恢复循环
- 条件判断集中于输入合法性校验，而不是分散在领域逻辑内部
- 通过工厂与解码器分工，避免将对象重建和文件读取混写在同一层

## 6. 设计约束与实现约定

### 6.1 接口设计约束

- 控制类对外暴露的方法优先返回结构化结果对象，再由适配器层转为 CLI 文本
- 同一业务动作只允许一个控制类作为主入口，避免重复控制
- 新增功能必须优先扩展策略或工厂，不得继续回写到 `GameEngine` 形成新的上帝类

### 6.2 异常处理约定

- 表现层优先将异常转换为可读提示
- 业务层只抛出明确的领域异常，如 `GameStateError`
- 基础设施层负责文件类异常和反序列化异常

### 6.3 测试追溯约定

后续测试用例至少覆盖以下接口：

- `CombatService.attack()` 的无敌人、普通命中、升级、击败 BOSS、死亡五类分支
- `InventoryService.take_item()` 的未 `look`、成功拾取、物品不存在三类分支
- `CheckpointService.respawn()` 的成功复活、无检查点失败两类分支
- `JsonSaveRepository.load()` 的合法存档、缺失文件、结构损坏三类分支

## 7. 维护建议

1. 任何新增业务能力都必须先确认归属控制类，再决定是否新增策略或工厂，不允许直接向 `GameEngine` 累积逻辑。
2. 若新增新的持久化方式，例如 SQLite 或云端存档，优先扩展 Repository 接口，不修改控制类对外方法签名。
3. 若新增新的输入方式，例如 GUI 按钮或 Web API，优先新增新的 Adapter，不修改 `GameEngine` 核心控制接口。
4. 每次 Sprint 结束后同步维护本 DDS 的“方法签名”和“关键算法图”两部分，保证文档与实现持续一致。

---

**DDS 更新结论**  
本次详细设计说明书完成了 Sprint 2 重构目标与阶段性成果的统一归档，明确了已落地能力与待落地接口，可作为 Sprint 3 代码落地、测试编写和维护协作的统一依据。
