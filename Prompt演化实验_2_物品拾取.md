# 实验 2: 物品拾取与背包 Mock 测试 Prompt 演化

## 背景
测试 `GameEngine.take_item` 方法，涉及房间状态（是否已搜索）、物品转移（从房间到玩家背包）以及边界情况（物品不存在、玩家已死亡）。

## 初始 Prompt
> 编写测试用例测试 `GameEngine.take_item`。要求测试拾取成功的场景。

## AI 输出的问题
1. **测试逻辑过于单一**：只测试了成功的情况，忽略了“未搜索（has_looked=False）”时无法拾取的业务规则。
2. **状态泄露**：没有正确隔离 `Player` 和 `Room` 的状态，导致测试用例之间可能相互影响。
3. **断言模糊**：只验证了返回的字符串是否包含“拿起了”，没有验证实体的状态（如房间里的物品是否真的减少了，玩家背包里是否真的增加了）。

## 改进后的 Prompt (Few-shot + 结构化指令)
> **任务：** 对 `GameEngine.take_item` 进行全路径覆盖测试。
>
> **业务规则：**
> 1. 玩家必须活着。
> 2. 房间必须先被 `look`（`has_looked=True`）。
> 3. 物品必须存在于房间中。
> 4. 拾取后，物品从房间 `items` 移除，加入玩家 `inventory`。
>
> **要求：**
> 1. **构造 3 个测试函数：**
>    - `test_take_item_success`: 成功拾取。
>    - `test_take_item_without_look`: 未搜索时拾取失败。
>    - `test_take_item_player_dead`: 玩家死亡时拾取失败。
> 2. **数据打桩：** 使用 `MagicMock` 模拟 `Item`、`Room` 和 `Player`。
> 3. **多重验证：** 验证返回的消息字符串，以及内部调用（如 `room.remove_item` 是否被调用，`player.add_item` 是否被调用）。
>
> **代码示例：**
> ```python
> def test_take_item_success(engine, mock_player, mock_room):
>     # 给定 room.has_looked = True, room.items 有 "Sword"
>     # 执行 ...
>     # 断言 ...
> ```

## 最终可用的测试代码
(将应用到 tests/test_engine_items_mock.py)
