"""MUD 游戏核心引擎"""
from datetime import datetime
from typing import Dict, Optional
from .models import Room, Player, Item, Enemy


class GameEngine:
    """游戏引擎 - 管理游戏状态和逻辑"""
    
    # BOSS 方向映射（每个房间指向 BOSS 房间的方向）
    BOSS_PATH = {
        "entrance": "north",
        "hall": "east",
        "goblin_camp": "east",
        "treasure": "north",
        "orc_hall": "north",
        "armory": "north",
    }
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player: Optional[Player] = None
        self.running = False
        self.game_won = False
        self.game_over = False
        self.checkpoint_room_id = ""
        self.checkpoint_time = ""
        self.last_death_time = ""
        self.last_respawn_time = ""

    def _now_str(self) -> str:
        """返回当前时间（用于存档和复活日志）。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _resolve_checkpoint_room(self) -> str:
        """解析可用检查点房间。"""
        if self.checkpoint_room_id in self.rooms:
            return self.checkpoint_room_id
        if "entrance" in self.rooms:
            return "entrance"
        if self.player and self.player.last_room in self.rooms:
            return self.player.last_room
        if self.player and self.player.current_room in self.rooms:
            return self.player.current_room
        if self.rooms:
            return next(iter(self.rooms))
        return ""

    def update_checkpoint(self, room_id: Optional[str] = None) -> None:
        """更新检查点（固定地点 + 固定时间）。"""
        if room_id and room_id in self.rooms:
            self.checkpoint_room_id = room_id
        elif self.player and self.player.current_room in self.rooms:
            self.checkpoint_room_id = self.player.current_room
        self.checkpoint_time = self._now_str()
    
    def add_room(self, room: Room) -> None:
        """添加房间到游戏世界"""
        self.rooms[room.id] = room
    
    def create_player(self, name: str, start_room: str) -> Player:
        """创建玩家"""
        if start_room not in self.rooms:
            raise ValueError(f"房间 {start_room} 不存在")
        self.player = Player(name=name, current_room=start_room)
        self.update_checkpoint(start_room)
        return self.player
    
    def get_current_room(self) -> Optional[Room]:
        """获取玩家当前房间"""
        if not self.player:
            return None
        return self.rooms.get(self.player.current_room)
    
    def get_boss_direction(self) -> str:
        """获取前往 BOSS 的方向"""
        if not self.player:
            return ""
        return self.BOSS_PATH.get(self.player.current_room, "")
    
    def move_player(self, direction: str) -> str:
        """移动玩家"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.is_alive:
            return "你已经死了，无法移动。输入 'respawn' 复活。"
        
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        if direction not in room.exits:
            boss_dir = self.get_boss_direction()
            hint = f"【提示】前往 BOSS 的方向是：{boss_dir}" if boss_dir else ""
            return f"不能往 {direction} 走。{room.get_exit_description(boss_dir)}\n{hint}"
        
        next_room_id = room.exits[direction]
        # 更新上一个房间
        self.player.last_room = self.player.current_room
        self.player.current_room = next_room_id
        
        new_room = self.rooms[next_room_id]
        result = [f"你前往{direction}...", "", self.describe_room()]
        
        # 检查是否有敌人
        if new_room.enemy and new_room.enemy.is_alive():
            result.append("")
            result.append(f"⚠️  {new_room.enemy.name}出现了！{new_room.enemy.description}")
            result.append(f"敌人 HP: {new_room.enemy.hp}/{new_room.enemy.max_hp} | 攻击力：{new_room.enemy.attack}")
            result.append("输入 'attack' 进行攻击！")
        
        return "\n".join(result)
    
    def describe_room(self) -> str:
        """描述当前房间（不显示物品，需要 look 才能发现）"""
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        desc = [f"=== {room.name} ===", room.description]
        
        # 显示敌人（如果有）
        if room.enemy and room.enemy.is_alive():
            desc.append(f"⚠️  这里有敌人：{room.enemy.name}！")
        
        # 显示出口和 BOSS 提示
        boss_dir = self.get_boss_direction()
        desc.append(room.get_exit_description(boss_dir))
        
        if boss_dir:
            desc.append(f"💡 【提示】前往最终 BOSS 的方向是：{boss_dir}")
        
        return "\n".join(desc)
    
    def look(self) -> str:
        """搜索房间（发现物品）"""
        if not self.player:
            return "游戏未开始。"
        
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        room.has_looked = True
        result = [f"你仔细搜索了 {room.name}..."]
        
        if room.items:
            item_names = ", ".join(item.name for item in room.items)
            result.append(f"🎁 你发现了：{item_names}")
        else:
            result.append("💭 这里没有什么值得拿的东西。")
        
        # 检查敌人
        if room.enemy and room.enemy.is_alive():
            result.append(f"⚠️  {room.enemy.name}正盯着你！")
        
        return "\n".join(result)
    
    def take_item(self, item_name: str) -> str:
        """拾取物品"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.is_alive:
            return "你已经死了，无法拾取物品。"
        
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        # 必须先 look 才能看到物品
        if not room.has_looked:
            return "这里看起来什么都没有。先输入 'look' 搜索一下！"
        
        item = room.remove_item(item_name)
        if item:
            self.player.add_item(item)
            if item.item_type == "weapon":
                return f"🎉 你拿起了 {item.name}！攻击力 +{item.effect}"
            elif item.item_type == "potion":
                return f"🎉 你拿起了 {item.name}！使用后可恢复 {item.effect} HP"
            else:
                return f"🎉 你拿起了 {item.name}。"
        else:
            return f"这里没有 '{item_name}'。"
    
    def show_inventory(self) -> str:
        """显示背包"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.inventory:
            return "🎒 背包是空的。"
        
        items = []
        for item in self.player.inventory:
            if item.item_type == "weapon":
                items.append(f"{item.name} (武器，攻击 +{item.effect})")
            elif item.item_type == "potion":
                items.append(f"{item.name} (药水，恢复 {item.effect} HP)")
            else:
                items.append(f"{item.name} ({item.description})")
        
        return "🎒 背包：" + ", ".join(items)
    
    def use_item(self, item_name: str) -> str:
        """使用物品"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.is_alive:
            return "你已经死了。"
        
        result = self.player.use_item(item_name)
        if result:
            return result
        return f"你没有 '{item_name}' 或者这个物品不能使用。"
    
    def attack_enemy(self) -> str:
        """攻击敌人"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.is_alive:
            return "你已经死了，无法攻击。"
        
        room = self.get_current_room()
        if not room or not room.enemy or not room.enemy.is_alive():
            return "这里没有敌人。"
        
        enemy = room.enemy
        
        # 玩家攻击
        player_dmg = self.player.get_attack_power()
        enemy.take_damage(player_dmg)
        result = [f"⚔️  你攻击了 {enemy.name}，造成 {player_dmg} 点伤害！"]
        
        if not enemy.is_alive():
            # 胜利
            self.player.xp += enemy.reward_xp
            result.append(f"🎉 你击败了 {enemy.name}！获得 {enemy.reward_xp} 经验值！")
            
            # 检查是否升级
            if self.player.xp >= self.player.level * 50:
                self.player.level_up()
                result.append(f"⭐ 升级了！当前等级：LV.{self.player.level}")
                result.append(f"   最大生命值 HP +20，且生命值已回满；攻击 +5")
            
            # 检查是否是 BOSS
            if room.is_boss_room:
                self.game_won = True
                result.append("")
                result.append("=" * 40)
                result.append("🏆 恭喜！你击败了最终 BOSS，游戏胜利！")
                result.append("=" * 40)
            
            room.enemy = None  # 移除敌人
        else:
            # 敌人反击
            enemy_dmg = enemy.attack
            self.player.take_damage(enemy_dmg)
            result.append(f"💥 {enemy.name}反击，对你造成 {enemy_dmg} 点伤害！")
            result.append(f"   你的 HP: {self.player.hp}/{self.player.max_hp}")
            
            if not self.player.is_alive:
                self.last_death_time = self._now_str()
                result.append("")
                result.append("💀 你被打败了...")
                result.append("你将回档到检查点。输入 'respawn' 继续游戏。")
        
        return "\n".join(result)
    
    def respawn(self) -> str:
        """复活"""
        if not self.player:
            return "游戏未开始。"
        
        if self.player.is_alive:
            return "你还活着，不需要复活。"
        
        checkpoint_room_id = self._resolve_checkpoint_room()
        if not checkpoint_room_id:
            return "❌ 复活失败：当前没有可用检查点。"

        self.player.current_room = checkpoint_room_id
        self.player.hp = self.player.max_hp // 2
        self.player.is_alive = True
        self.last_respawn_time = self._now_str()

        room = self.get_current_room()
        checkpoint_time = self.checkpoint_time or "未知时间"
        return (
            f"✨ 你复活了！回到检查点：{room.name}（记录时间：{checkpoint_time}）\n"
            f"HP 恢复到 {self.player.hp}/{self.player.max_hp}"
        )
    
    def show_stats(self) -> str:
        """显示玩家状态"""
        if not self.player:
            return "游戏未开始。"
        return "📊 " + self.player.get_stats()
    
    def save_game(self, filename: str) -> str:
        """保存游戏"""
        import json
        
        if not self.player:
            return "游戏未开始。"
        
        # 每次手动保存都更新检查点位置和时间
        self.update_checkpoint()

        data = {
            "player": {
                "name": self.player.name,
                "current_room": self.player.current_room,
                "last_room": self.player.last_room,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "attack": self.player.attack,
                "xp": self.player.xp,
                "level": self.player.level,
                "inventory": [
                    {"name": item.name, "type": item.item_type, "effect": item.effect}
                    for item in self.player.inventory
                ]
            },
            "meta": {
                "checkpoint_room_id": self.checkpoint_room_id,
                "checkpoint_time": self.checkpoint_time,
                "last_death_time": self.last_death_time,
                "last_respawn_time": self.last_respawn_time,
            },
            "rooms": {}
        }
        
        # 保存房间状态（敌人是否被击败）
        for room_id, room in self.rooms.items():
            data["rooms"][room_id] = {
                "has_looked": room.has_looked,
                "enemy_alive": room.enemy.is_alive() if room.enemy else None,
                "items": [item.name for item in room.items]
            }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return f"💾 游戏已保存到 {filename}"
    
    def load_game(self, filename: str) -> str:
        """加载游戏"""
        import json
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            player_data = data["player"]
            self.player = Player(
                name=player_data["name"],
                current_room=player_data["current_room"],
                last_room=player_data.get("last_room", ""),
                hp=player_data["hp"],
                max_hp=player_data["max_hp"],
                attack=player_data["attack"],
                xp=player_data["xp"],
                level=player_data["level"],
                inventory=[]
            )
            
            # 恢复物品
            for item_data in player_data["inventory"]:
                item = Item(
                    name=item_data["name"],
                    description="",
                    item_type=item_data.get("type", "tool"),
                    effect=item_data.get("effect", 0)
                )
                self.player.add_item(item)
            
            # 恢复房间状态
            for room_id, room_data in data.get("rooms", {}).items():
                if room_id in self.rooms:
                    self.rooms[room_id].has_looked = room_data.get("has_looked", False)

            # 恢复检查点和死亡/复活时间
            meta_data = data.get("meta", {})
            loaded_checkpoint_room = meta_data.get("checkpoint_room_id", "")
            if loaded_checkpoint_room in self.rooms:
                self.checkpoint_room_id = loaded_checkpoint_room
            else:
                self.checkpoint_room_id = self.player.current_room

            self.checkpoint_time = meta_data.get("checkpoint_time", "")
            if not self.checkpoint_time:
                self.checkpoint_time = self._now_str()

            self.last_death_time = meta_data.get("last_death_time", "")
            self.last_respawn_time = meta_data.get("last_respawn_time", "")
            
            return f"💾 游戏已从 {filename} 加载。欢迎回来，{self.player.name}！"
        except FileNotFoundError:
            return f"❌ 存档文件 {filename} 不存在。"
        except Exception as e:
            return f"❌ 加载失败：{e}"
