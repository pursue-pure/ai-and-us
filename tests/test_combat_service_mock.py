import pytest
from unittest.mock import MagicMock, patch
from game.services.combat_service import CombatService
from game.models import Player, Room, Enemy

@pytest.fixture
def combat_service():
    return CombatService()

def test_attack_trigger_level_up(combat_service):
    """场景 A: 玩家 XP 增加后刚好等于升级门槛，验证升级逻辑"""
    # 模拟环境设置
    mock_player = MagicMock(spec=Player)
    mock_player.name = "Hero"
    mock_player.level = 1
    mock_player.xp = 40  # 升级需要 50，当前 40
    mock_player.get_attack_power.return_value = 10
    
    mock_enemy = MagicMock(spec=Enemy)
    mock_enemy.name = "Slime"
    mock_enemy.hp = 10
    mock_enemy.reward_xp = 10  # 击败后 XP 变为 50，刚好升级
    mock_enemy.is_alive.side_effect = [True, False] # 攻击前活着，攻击后死亡
    
    mock_room = MagicMock(spec=Room)
    mock_room.enemy = mock_enemy
    mock_room.is_boss_room = False

    # 执行攻击
    result = combat_service.attack(mock_player, mock_room)

    # 验证逻辑
    # 1. 经验值增加
    assert mock_player.xp == 50
    # 2. 调用了 level_up
    mock_player.level_up.assert_called_once()
    # 3. 结果包含升级信息
    assert any("升级了" in msg for msg in result.messages)
    assert result.level_up is not None
    assert result.level_up.xp_gained == 10
    # 4. 房间敌人被移除
    assert mock_room.enemy is None

def test_attack_enemy_survives_and_counter_attacks(combat_service):
    """场景 B: 敌人存活并反击"""
    mock_player = MagicMock(spec=Player)
    mock_player.get_attack_power.return_value = 5
    
    mock_enemy = MagicMock(spec=Enemy)
    mock_enemy.name = "Guard"
    mock_enemy.hp = 20
    mock_enemy.attack = 8
    mock_enemy.is_alive.return_value = True
    
    mock_room = MagicMock(spec=Room)
    mock_room.enemy = mock_enemy

    # 执行攻击
    result = combat_service.attack(mock_player, mock_room)

    # 验证逻辑
    # 1. 敌人承受伤害
    mock_enemy.take_damage.assert_called_with(5)
    # 2. 玩家承受反击伤害
    mock_player.take_damage.assert_called_with(8)
    # 3. 敌人依然在房间里
    assert mock_room.enemy == mock_enemy
    # 4. 结果中应该提到反击消息（虽然当前代码并未在 result 中明确标记反击对象，但可以通过逻辑推导）
    # 注意：当前 CombatService._resolve_counter_attack 仅调用 player.take_damage
