import pytest
from game.snapshot import GameSnapshot, PlayerSnapshot, RoomSnapshot, ItemSnapshot, EnemySnapshot
from game.models import Player, Room, Enemy, Item

def test_snapshot_symmetry_simple():
    """测试简单的快照序列化和反序列化对称性"""
    raw_data = {
        "player": {
            "name": "Hero",
            "current_room": "start",
            "hp": 100,
            "max_hp": 100,
            "level": 1,
            "xp": 0,
            "inventory": []
        },
        "rooms": {
            "start": {
                "id": "start",
                "has_looked": True,
                "item_details": [
                    {"name": "Sword", "description": "Sharp", "item_type": "weapon", "effect": 5}
                ],
                "enemy": None
            }
        },
        "meta": {"current_room": "start"}
    }
    
    snapshot = GameSnapshot.from_dict(raw_data)
    exported = snapshot.to_dict()
    
    # 验证关键数据的一致性
    assert exported["player"]["name"] == "Hero"
    assert exported["player"]["current_room"] == "start"
    assert len(exported["rooms"]["start"]["item_details"]) == 1
    assert exported["rooms"]["start"]["item_details"][0]["name"] == "Sword"

def test_snapshot_with_complex_enemy():
    """测试带有敌人和复杂物品的快照转换"""
    enemy_data = {
        "name": "Slime",
        "hp": 20,
        "max_hp": 20,
        "attack": 3,
        "reward_xp": 10,
        "is_alive": True
    }
    enemy_snapshot = EnemySnapshot.from_dict(enemy_data)
    
    room_snapshot = RoomSnapshot(
        id="forest",
        name="Dark Forest",
        description="A dark place",
        items=[],
        enemy=enemy_snapshot,
        has_looked=True
    )
    
    game_dict = {
        "player": {"name": "A", "current_room": "forest", "hp": 50, "max_hp": 50, "level": 2, "xp": 20, "inventory": []},
        "rooms": {"forest": room_snapshot.to_dict()},
        "meta": {"current_room": "forest"}
    }
    
    rebuilt = GameSnapshot.from_dict(game_dict)
    assert rebuilt.rooms["forest"].enemy.name == "Slime"
    assert rebuilt.rooms["forest"].enemy.hp > 0

def test_player_model_to_snapshot():
    """测试将 Player 领域模型转换为 Snapshot 模型"""
    player = Player(name="TDD_Tester", current_room="start", hp=80, max_hp=100)
    player.level = 5
    player.xp = 500
    
    # 手动创建 Snapshot 模拟 engine._build_player_snapshot 的逻辑
    snapshot = PlayerSnapshot(
        name=player.name,
        current_room=player.current_room,
        hp=player.hp,
        max_hp=player.max_hp,
        level=player.level,
        xp=player.xp,
        inventory=[]
    )
    
    p_dict = snapshot.to_dict()
    assert p_dict["level"] == 5
    assert p_dict["name"] == "TDD_Tester"
    assert p_dict["current_room"] == "start"
