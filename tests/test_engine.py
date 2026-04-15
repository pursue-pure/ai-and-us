"""MUD 游戏引擎测试"""
import json
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

    def test_boss_direction_for_treasure_should_be_north(self, engine):
        engine.player.current_room = "treasure"
        assert engine.get_boss_direction() == "north"
    
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

    def test_respawn_back_to_checkpoint(self, engine, tmp_path):
        # 先移动并保存，形成固定检查点
        engine.move_player("north")
        save_file = tmp_path / "checkpoint_save.json"
        engine.save_game(str(save_file))

        checkpoint_room = engine.checkpoint_room_id
        checkpoint_time = engine.checkpoint_time

        # 模拟死亡
        engine.player.hp = 0
        engine.player.is_alive = False
        engine.player.current_room = "room1"

        result = engine.respawn()

        assert checkpoint_room == "room2"
        assert engine.player.current_room == checkpoint_room
        assert "回到检查点" in result
        assert checkpoint_time in result

    def test_load_restore_checkpoint_meta(self, engine, tmp_path):
        engine.move_player("north")
        save_file = tmp_path / "checkpoint_meta.json"
        engine.save_game(str(save_file))

        # 污染内存中的检查点，再通过 load 恢复
        engine.checkpoint_room_id = "room1"
        engine.checkpoint_time = "2000-01-01 00:00:00"

        engine.load_game(str(save_file))

        assert engine.checkpoint_room_id == "room2"
        assert engine.checkpoint_time != "2000-01-01 00:00:00"

        with open(save_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["meta"]["checkpoint_room_id"] == "room2"

    def test_load_restores_enemy_dead_state(self, tmp_path):
        """读档后已击败的敌人应保持死亡状态（hp == 0）"""
        from game.models import Enemy
        eng = GameEngine()
        enemy = Enemy(name="哥布林", description="", hp=20, max_hp=20, attack=5, reward_xp=30)
        room1 = Room(id="room1", name="房间1", description="", exits={"north": "room2"},
                     enemy=enemy)
        room2 = Room(id="room2", name="房间2", description="", exits={"south": "room1"})
        eng.add_room(room1)
        eng.add_room(room2)
        eng.create_player("测试", "room1")

        # 模拟击败敌人
        eng.rooms["room1"].enemy.hp = 0
        save_file = tmp_path / "enemy_dead.json"
        eng.save_game(str(save_file))

        # 重置敌人血量，模拟重新加载
        eng.rooms["room1"].enemy.hp = 20
        eng.load_game(str(save_file))

        assert eng.rooms["room1"].enemy.hp == 0

    def test_load_restores_room_items(self, tmp_path):
        """读档后已拾取的物品不应重新出现"""
        from game.models import Item
        eng = GameEngine()
        room1 = Room(id="room1", name="房间1", description="", exits={"north": "room2"},
                     items=[Item("铁剑", "一把剑", "weapon", 8),
                            Item("生命药水", "一瓶药水", "potion", 25)])
        room2 = Room(id="room2", name="房间2", description="", exits={"south": "room1"})
        eng.add_room(room1)
        eng.add_room(room2)
        eng.create_player("测试", "room1")

        # 模拟拾取铁剑
        eng.rooms["room1"].has_looked = True
        eng.take_item("铁剑")
        save_file = tmp_path / "items.json"
        eng.save_game(str(save_file))

        # 重置房间物品，模拟重新加载
        eng.rooms["room1"].items = [Item("铁剑", "一把剑", "weapon", 8),
                                    Item("生命药水", "一瓶药水", "potion", 25)]
        eng.load_game(str(save_file))

        item_names = [i.name for i in eng.rooms["room1"].items]
        assert "铁剑" not in item_names
        assert "生命药水" in item_names


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

    def test_take_with_angle_brackets(self, handler):
        handler.engine.rooms["start"].add_item(Item("铁剑", "一把锋利的铁剑", "weapon", 8))
        handler.engine.rooms["start"].has_looked = True

        result = handler.handle("take <铁剑>")
        assert "拿起了" in result
        assert handler.engine.player.has_item("铁剑")

    def test_take_without_space_before_brackets(self, handler):
        handler.engine.rooms["start"].add_item(Item("铁剑", "一把锋利的铁剑", "weapon", 8))
        handler.engine.rooms["start"].has_looked = True

        result = handler.handle("take<铁剑>")
        assert "拿起了" in result
        assert handler.engine.player.has_item("铁剑")

    def test_take_compact_command(self, handler):
        handler.engine.rooms["start"].add_item(Item("铁剑", "一把锋利的铁剑", "weapon", 8))
        handler.engine.rooms["start"].has_looked = True

        result = handler.handle("take铁剑")
        assert "拿起了" in result
        assert handler.engine.player.has_item("铁剑")
