# 实验 1: 战斗计算 Mock 测试 Prompt 演化

## 背景
测试 `CombatService.attack` 方法在玩家击败敌人并升级时的逻辑。

## 初始 Prompt
> 请为 `CombatService.attack` 编写单元测试，使用 pytest 和 mock。测试玩家攻击敌人，敌人死亡并触发玩家升级的情况。

## AI 输出的问题
1. **重言式测试**：AI 编写的代码只是简单地重复了业务逻辑。例如，断言 `player.level` 变成了 `old_level + 1`，但没有验证具体的属性值（如 `max_hp` 的增加）。
2. **缺乏边界覆盖**：没有测试刚好达到升级经验值（XP == level * 50）和刚好差一分升级的情况。
3. **Mock 不彻底**：直接使用了真实的对象而不是 Mock，导致测试变得脆弱，依赖于 `Player` 和 `Room` 的内部实现。

## 改进后的 Prompt (结构化指令 + Few-shot + 角色扮演)
> **角色：** 你是一位追求 100% 关键逻辑覆盖率的资深测试工程师。
>
> **任务：** 为 `CombatService.attack` 编写严谨的 Mock 单元测试。
>
> **上下文：**
> - `CombatService` 负责结算伤害、处理胜利（XP 增加、升级检测）和反击。
> - 升级公式：`player.xp >= player.level * 50`。
>
> **要求：**
> 1. **使用 Mock：** 使用 `unittest.mock` 对 `Player`、`Room` 和 `Enemy` 进行打桩（Stubbing）。
> 2. **边界测试（CoT）：**
>    - 场景 A：玩家 XP 增加后刚好等于升级门槛（例如 level 1, xp 50）。
>    - 场景 B：玩家攻击后，敌人的 HP 刚好降为 0。
> 3. **行为验证：** 不仅要验证 `CombatResult` 的返回值，还要验证 `player.level_up()` 是否被调用，以及消息列表中是否包含特定的提示词。
> 4. **代码示例格式：**
> ```python
> def test_attack_trigger_level_up(mock_player, mock_room):
>     # 给定 ...
>     # 执行 ...
>     # 断言 ...
> ```

## 最终可用的测试代码
(将直接应用到 tests/test_combat_service_evolution.py)
