"""MUD 游戏核心引擎"""
from typing import Dict, Optional
from .models import Room, Player, Item


class GameEngine:
    """游戏引擎 - 管理游戏状态和逻辑"""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player: Optional[Player] = None
        self.running = False
    
    def add_room(self, room: Room) -> None:
        """添加房间到游戏世界"""
        self.rooms[room.id] = room
    
    def create_player(self, name: str, start_room: str) -> Player:
        """创建玩家"""
        if start_room not in self.rooms:
            raise ValueError(f"房间 {start_room} 不存在")
        self.player = Player(name=name, current_room=start_room)
        return self.player
    
    def get_current_room(self) -> Optional[Room]:
        """获取玩家当前房间"""
        if not self.player:
            return None
        return self.rooms.get(self.player.current_room)
    
    def move_player(self, direction: str) -> str:
        """移动玩家"""
        if not self.player:
            return "游戏未开始。"
        
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        if direction not in room.exits:
            return f"不能往 {direction} 走。{room.get_exit_description()}"
        
        next_room_id = room.exits[direction]
        self.player.current_room = next_room_id
        new_room = self.rooms[next_room_id]
        
        return f"你前往{direction}...\n\n{self.describe_room()}"
    
    def describe_room(self) -> str:
        """描述当前房间"""
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        desc = [f"=== {room.name} ===", room.description]
        
        if room.items:
            item_names = ", ".join(item.name for item in room.items)
            desc.append(f"你看到：{item_names}")
        
        desc.append(room.get_exit_description())
        return "\n".join(desc)
    
    def take_item(self, item_name: str) -> str:
        """拾取物品"""
        if not self.player:
            return "游戏未开始。"
        
        room = self.get_current_room()
        if not room:
            return "你在虚空中..."
        
        item = room.remove_item(item_name)
        if item:
            self.player.add_item(item)
            return f"你拿起了 {item.name}。"
        else:
            return f"这里没有 '{item_name}'。"
    
    def show_inventory(self) -> str:
        """显示背包"""
        if not self.player:
            return "游戏未开始。"
        
        if not self.player.inventory:
            return "背包是空的。"
        
        items = ", ".join(item.name for item in self.player.inventory)
        return f"背包：{items}"
    
    def save_game(self, filename: str) -> str:
        """保存游戏"""
        import json
        
        if not self.player:
            return "游戏未开始。"
        
        data = {
            "player": {
                "name": self.player.name,
                "current_room": self.player.current_room,
                "inventory": [item.name for item in self.player.inventory]
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return f"游戏已保存到 {filename}"
    
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
                inventory=[]
            )
            
            # 重建物品
            all_items = {}
            for room in self.rooms.values():
                for item in room.items:
                    all_items[item.name.lower()] = item
            
            for item_name in player_data["inventory"]:
                if item_name.lower() in all_items:
                    self.player.add_item(all_items[item_name.lower()])
            
            return f"游戏已从 {filename} 加载。欢迎回来，{self.player.name}！"
        except FileNotFoundError:
            return f"存档文件 {filename} 不存在。"
        except Exception as e:
            return f"加载失败：{e}"
