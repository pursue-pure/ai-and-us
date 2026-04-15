"""CombatService 单元测试"""
import pytest
from game.services.combat_service import CombatService
from game.models import Player, Room, Enemy, Item


@pytest.fixture
def player():
    return Player(name="测试玩家", current_room="room1", hp=50, max_hp=50, attack=10)


@pytest.fixture
def weak_enemy():
    """弱敌人 — 一击必杀，用于测试胜利分支"""
    return Enemy(name="哥布林", description="", hp=5, max_hp=5, attack=5, reward_xp=30)


@pytest.fixture
def strong_enemy():
    """强敌人 — 打不死，用于测试反击分支"""
    return Enemy(name="兽人", description="", hp=100, max_hp=100, attack=5, reward_xp=60)


@pytest.fixture
def lethal_enemy():
    """致命敌人 — 反击一击杀死玩家"""
    return Enemy(name="巨龙", description="", hp=100, max_hp=100, attack=50, reward_xp=500)


def make_room(enemy=None, is_boss=False):
    return Room(id="r1", name="测试房间", description="", enemy=enemy, is_boss_room=is_boss)


class TestCombatService:

    def test_no_enemy_raises_on_none(self, player):
        """attack() 调用方（GameEngine）负责前置校验，CombatService 本身不处理无敌人情况"""
        service = CombatService()
        room = make_room(enemy=None)
        # GameEngine 在调用前已校验，此处验证 enemy 为 None 时会抛出 AttributeError
        with pytest.raises(AttributeError):
            service.attack(player, room)

    def test_normal_hit_enemy_survives(self, player, strong_enemy):
        """普通命中 — 敌人存活，触发反击"""
        service = CombatService()
        room = make_room(enemy=strong_enemy)
        result = service.attack(player, room)

        assert result.player_damage == 10
        assert result.enemy_alive is True
        assert result.counter_attack is not None
        assert result.counter_attack.damage == 5
        assert result.player_dead is False
        assert result.boss_victory is False
        assert result.level_up is None
        assert any("反击" in m for m in result.messages)

    def test_victory_and_level_up(self, player, weak_enemy):
        """击败敌人且经验达标 — 触发升级"""
        player.xp = 20  # 再加 30 xp = 50 >= level(1) * 50，触发升级
        service = CombatService()
        room = make_room(enemy=weak_enemy)
        result = service.attack(player, room)

        assert result.enemy_alive is False
        assert result.level_up is not None
        assert result.level_up.new_level == 2
        assert result.level_up.xp_gained == 30
        assert player.level == 2
        assert room.enemy is None
        assert any("升级" in m for m in result.messages)

    def test_boss_victory(self, player):
        """击败 BOSS 房间敌人 — 触发 boss_victory 标志"""
        boss = Enemy(name="远古巨龙", description="", hp=1, max_hp=100, attack=5, reward_xp=500)
        service = CombatService()
        room = make_room(enemy=boss, is_boss=True)
        result = service.attack(player, room)

        assert result.boss_victory is True
        assert result.enemy_alive is False
        assert any("BOSS" in m or "胜利" in m for m in result.messages)

    def test_player_dead_after_counter_attack(self, player, lethal_enemy):
        """敌人反击致死 — player_dead=True，记录死亡时间"""
        service = CombatService()
        room = make_room(enemy=lethal_enemy)
        result = service.attack(player, room)

        assert result.player_dead is True
        assert result.counter_attack.player_dead is True
        assert player.is_alive is False
        assert service.last_death_time != ""
        assert any("打败" in m for m in result.messages)
