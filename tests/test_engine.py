"""MUD 游戏引擎测试"""
import pytest
from game.engine import GameEngine
from game.models import Room, Item, Player


class TestRoom:
    """房间测试"""
    
    def test_room_creation(self):
        room = Room(id="test", name="测试房间", description="这是一个测试房间")
        assert room.id == "test"
        assert room.name == "测试房间"
        assert room.exits == {}
        assert room.items == []
    
    def test_room_add_item(self):
        room = Room(id="test", name="测试房间", description="描述")
        item = Item("剑", "一把剑")
        room.add_item(item)
        assert len(room.items) == 1
        assert room.items[0].name == "剑"
    
    def test_room_remove_item(self):
        room = Room(id="test", name="测试房间", description="描述")
        item = Item("剑", "一把剑")
        room.add_item(item)
        
        removed = room.remove_item("剑")
        assert removed is not None
        assert removed.name == "剑"
        assert len(room.items) == 0


class TestPlayer:
    """玩家测试"""
    
    def test_player_creation(self):
        player = Player(name="英雄", current_room="start")
        assert player.name == "英雄"
        assert player.current_room == "start"
        assert player.inventory == []
    
    def test_player_add_item(self):
        player = Player(name="英雄", current_room="start")
        item = Item("盾牌", "一个木盾")
        player.add_item(item)
        assert len(player.inventory) == 1
        assert player.has_item("盾牌")


class TestGameEngine:
    """游戏引擎测试"""
    
    @pytest.fixture
    def engine(self):
        """创建测试用引擎"""
        eng = GameEngine()
        room1 = Room(id="room1", name="房间 1", description="描述 1", exits={"north": "room2"})
        room2 = Room(id="room2", name="房间 2", description="描述 2", exits={"south": "room1"})
        eng.add_room(room1)
        eng.add_room(room2)
        eng.create_player("测试玩家", "room1")
        return eng
    
    def test_get_current_room(self, engine):
        room = engine.get_current_room()
        assert room is not None
        assert room.id == "room1"
    
    def test_move_player_success(self, engine):
        result = engine.move_player("north")
        assert "房间 2" in result
        assert engine.player.current_room == "room2"
    
    def test_move_player_invalid_direction(self, engine):
        result = engine.move_player("west")
        assert "不能往 west 走" in result
    
    def test_take_item(self, engine):
        engine.rooms["room1"].add_item(Item("金币", "一些金币"))
        # 必须先 look 才能看到物品
        engine.rooms["room1"].has_looked = True
        result = engine.take_item("金币")
        assert "拿起了" in result or "金币" in result
        assert engine.player.has_item("金币")
    
    def test_inventory_empty(self, engine):
        result = engine.show_inventory()
        assert "空的" in result
    
    def test_inventory_with_items(self, engine):
        engine.player.add_item(Item("剑", "一把剑"))
        result = engine.show_inventory()
        assert "剑" in result


class TestCommandHandler:
    """命令处理器测试"""
    
    @pytest.fixture
    def handler(self):
        """创建测试用命令处理器"""
        from game.commands import CommandHandler
        engine = GameEngine()
        room = Room(id="start", name="起点", description="起点房间", exits={"north": "north_room"})
        engine.add_room(room)
        engine.create_player("测试", "start")
        return CommandHandler(engine)
    
    def test_help_command(self, handler):
        result = handler.handle("help")
        assert "移动" in result
    
    def test_look_command(self, handler):
        result = handler.handle("look")
        assert "起点" in result
    
    def test_unknown_command(self, handler):
        result = handler.handle("foobar")
        assert "未知命令" in result
    
    def test_empty_input(self, handler):
        result = handler.handle("")
        assert "请输入命令" in result
