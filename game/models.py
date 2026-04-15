"""MUD 游戏数据模型"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def _normalize_item_name(name: str) -> str:
    """规范化物品名，提升输入容错。"""
    return name.strip().lower().strip("<>").replace(" ", "")


@dataclass
class Item:
    """物品"""
    name: str
    description: str
    item_type: str = "tool"  # tool, weapon, potion
    effect: int = 0  # 效果值（攻击力或治疗量）
    
    def __str__(self) -> str:
        return self.name


@dataclass
class Enemy:
    """敌人"""
    name: str
    description: str
    hp: int
    max_hp: int
    attack: int
    reward_xp: int = 10
    
    def is_alive(self) -> bool:
        return self.hp > 0
    
    def take_damage(self, damage: int) -> int:
        """承受伤害，返回实际伤害值"""
        self.hp = max(0, self.hp - damage)
        return damage


@dataclass
class Room:
    """房间"""
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)  # direction -> room_id
    items: List[Item] = field(default_factory=list)
    enemy: Optional[Enemy] = None
    is_boss_room: bool = False
    has_looked: bool = False  # 是否已经搜索过
    last_room: str = ""  # 上一个房间 ID（用于复活）
    
    def add_item(self, item: Item) -> None:
        self.items.append(item)
    
    def remove_item(self, item_name: str) -> Optional[Item]:
        target_name = _normalize_item_name(item_name)
        for i, item in enumerate(self.items):
            if _normalize_item_name(item.name) == target_name:
                return self.items.pop(i)
        return None
    
    def get_exit_description(self, boss_direction: str = "") -> str:
        if not self.exits:
            return "这里没有出口。"
        directions = []
        for dir, room_id in self.exits.items():
            if boss_direction and dir == boss_direction:
                directions.append(f"{dir}【前往 BOSS】")
            else:
                directions.append(dir)
        return "出口：" + ", ".join(directions)


@dataclass
class Player:
    """玩家"""
    name: str
    current_room: str
    last_room: str = ""  # 上一个房间（用于复活）
    hp: int = 50
    max_hp: int = 50
    attack: int = 10
    inventory: List[Item] = field(default_factory=list)
    xp: int = 0
    level: int = 1
    is_alive: bool = True
    
    def add_item(self, item: Item) -> None:
        self.inventory.append(item)
    
    def has_item(self, item_name: str) -> bool:
        target_name = _normalize_item_name(item_name)
        return any(_normalize_item_name(item.name) == target_name for item in self.inventory)
    
    def get_attack_power(self) -> int:
        """获取总攻击力（基础 + 装备）"""
        bonus = sum(item.effect for item in self.inventory if item.item_type == "weapon")
        return self.attack + bonus
    
    def take_damage(self, damage: int) -> int:
        """承受伤害"""
        self.hp = max(0, self.hp - damage)
        if self.hp == 0:
            self.is_alive = False
        return damage
    
    def heal(self, amount: int) -> int:
        """治疗，返回实际治疗量"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old_hp
    
    def level_up(self) -> None:
        """升级"""
        self.level += 1
        self.max_hp += 20
        self.hp = self.max_hp
        self.attack += 5
    
    def use_item(self, item_name: str) -> Optional[str]:
        """使用物品，返回使用效果描述"""
        target_name = _normalize_item_name(item_name)
        for i, item in enumerate(self.inventory):
            if _normalize_item_name(item.name) == target_name:
                if item.item_type == "potion":
                    healed = self.heal(item.effect)
                    self.inventory.pop(i)
                    return f"你使用了 {item.name}，恢复了 {healed} 点 HP。"
                elif item.item_type == "weapon":
                    return f"你装备了 {item.name}，攻击力 +{item.effect}。"
        return None
    
    def get_stats(self) -> str:
        """获取玩家状态"""
        return (f"LV.{self.level} {self.name} | "
                f"HP: {self.hp}/{self.max_hp} | "
                f"攻击：{self.get_attack_power()} | "
                f"经验：{self.xp}")
