"""MUD 游戏数据模型"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Item:
    """物品"""
    name: str
    description: str
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Room:
    """房间"""
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    items: List[Item] = field(default_factory=list)
    
    def add_item(self, item: Item) -> None:
        self.items.append(item)
    
    def remove_item(self, item_name: str) -> Optional[Item]:
        for i, item in enumerate(self.items):
            if item.name.lower() == item_name.lower():
                return self.items.pop(i)
        return None
    
    def get_exit_description(self) -> str:
        if not self.exits:
            return "这里没有出口。"
        directions = ", ".join(self.exits.keys())
        return f"出口：{directions}"


@dataclass
class Player:
    """玩家"""
    name: str
    current_room: str
    inventory: List[Item] = field(default_factory=list)
    
    def add_item(self, item: Item) -> None:
        self.inventory.append(item)
    
    def has_item(self, item_name: str) -> bool:
        return any(item.name.lower() == item_name.lower() for item in self.inventory)
