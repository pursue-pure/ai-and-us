import pytest
from unittest.mock import MagicMock
from game.engine import GameEngine
from game.models import Player, Room, Item

@pytest.fixture
def engine():
    return GameEngine()

def test_take_item_success(engine):
    """成功拾取物品：已搜索且物品存在"""
    # Setup
    mock_item = MagicMock(spec=Item)
    mock_item.name = "Sword"
    mock_item.item_type = "weapon"
    mock_item.effect = 5

    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = True
    
    # 模拟房间
    mock_room = MagicMock(spec=Room)
    mock_room.has_looked = True
    mock_room.remove_item.return_value = mock_item
    
    engine.player = mock_player
    engine.rooms = {"start": mock_room}
    mock_player.current_room = "start"

    # Execute
    result = engine.take_item("Sword")

    # Assert
    assert "拿起了 Sword" in result
    mock_room.remove_item.assert_called_with("Sword")
    mock_player.add_item.assert_called_with(mock_item)

def test_take_item_without_look(engine):
    """拾取失败：未先搜索房间"""
    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = True
    
    mock_room = MagicMock(spec=Room)
    mock_room.has_looked = False  # 关键点
    
    engine.player = mock_player
    engine.rooms = {"start": mock_room}
    mock_player.current_room = "start"

    # Execute
    result = engine.take_item("Sword")

    # Assert
    assert "先输入 'look' 搜索一下" in result
    mock_room.remove_item.assert_not_called()
    mock_player.add_item.assert_not_called()

def test_take_item_player_dead(engine):
    """拾取失败：玩家已死亡"""
    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = False # 死亡
    
    engine.player = mock_player

    # Execute
    result = engine.take_item("Sword")

    # Assert
    assert "你已经死了" in result
    # 甚至不需要查找房间

def test_engine_move_player_dead(engine):
    """引擎测试：玩家死亡无法移动"""
    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = False
    engine.player = mock_player
    assert "已经死了" in engine.move_player("north")

def test_engine_move_no_exit(engine):
    """引擎测试：移动到不存在的方向"""
    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = True
    mock_player.current_room = "start"
    
    mock_room = MagicMock(spec=Room)
    mock_room.exits = {"north": "hall"}
    mock_room.get_exit_description.return_value = "Exits: north"
    
    engine.player = mock_player
    engine.rooms = {"start": mock_room}
    
    assert "不能往 south 走" in engine.move_player("south")

def test_engine_describe_room_with_boss_hint(engine):
    """引擎测试：房间描述包含 BOSS 提示"""
    mock_player = MagicMock(spec=Player)
    mock_player.current_room = "entrance"
    engine.player = mock_player
    
    mock_room = MagicMock(spec=Room)
    mock_room.name = "Entrance"
    mock_room.description = "A path."
    mock_room.enemy = None
    mock_room.get_exit_description.return_value = "Exits: north"
    
    engine.rooms = {"entrance": mock_room}
    
    desc = engine.describe_room()
    assert "BOSS" in desc
    assert "north" in desc

def test_engine_use_item_fail(engine):
    """引擎测试：使用不存在的物品"""
    mock_player = MagicMock(spec=Player)
    mock_player.is_alive = True
    mock_player.use_item.return_value = None
    engine.player = mock_player
    
    assert "你没有" in engine.use_item("nonexistent")
