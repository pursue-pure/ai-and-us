"""游戏快照模型。"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ItemSnapshot:
    name: str
    description: str
    item_type: str = "tool"
    effect: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.item_type,
            "effect": self.effect,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemSnapshot":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            item_type=data.get("type", data.get("item_type", "tool")),
            effect=data.get("effect", 0),
        )


@dataclass
class EnemySnapshot:
    name: str
    description: str
    hp: int
    max_hp: int
    attack: int
    reward_xp: int = 10

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "reward_xp": self.reward_xp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnemySnapshot":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            hp=data.get("hp", 0),
            max_hp=data.get("max_hp", data.get("hp", 0)),
            attack=data.get("attack", 0),
            reward_xp=data.get("reward_xp", 10),
        )


@dataclass
class PlayerSnapshot:
    name: str
    current_room: str
    last_room: str = ""
    hp: int = 50
    max_hp: int = 50
    attack: int = 10
    inventory: List[ItemSnapshot] = field(default_factory=list)
    xp: int = 0
    level: int = 1
    is_alive: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "current_room": self.current_room,
            "last_room": self.last_room,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "attack": self.attack,
            "xp": self.xp,
            "level": self.level,
            "is_alive": self.is_alive,
            "inventory": [item.to_dict() for item in self.inventory],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerSnapshot":
        inventory_data = data.get("inventory_details") or data.get("inventory") or []
        inventory = []
        for item_data in inventory_data:
            if isinstance(item_data, dict):
                inventory.append(ItemSnapshot.from_dict(item_data))
            else:
                inventory.append(ItemSnapshot(name=str(item_data), description=""))

        return cls(
            name=data["name"],
            current_room=data["current_room"],
            last_room=data.get("last_room", ""),
            hp=data.get("hp", 50),
            max_hp=data.get("max_hp", 50),
            attack=data.get("attack", 10),
            inventory=inventory,
            xp=data.get("xp", 0),
            level=data.get("level", 1),
            is_alive=data.get("is_alive", data.get("hp", 1) > 0),
        )


@dataclass
class RoomSnapshot:
    id: str
    name: str
    description: str
    exits: Dict[str, str] = field(default_factory=dict)
    items: List[ItemSnapshot] = field(default_factory=list)
    enemy: Optional[EnemySnapshot] = None
    is_boss_room: bool = False
    has_looked: bool = False
    last_room: str = ""

    def to_dict(self) -> dict[str, Any]:
        enemy_data = self.enemy.to_dict() if self.enemy else None
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "exits": dict(self.exits),
            "has_looked": self.has_looked,
            "is_boss_room": self.is_boss_room,
            "last_room": self.last_room,
            "items": [item.name for item in self.items],
            "item_details": [item.to_dict() for item in self.items],
            "enemy_alive": (self.enemy.hp > 0) if self.enemy else None,
            "enemy_hp": self.enemy.hp if self.enemy else None,
            "enemy_name": self.enemy.name if self.enemy else None,
            "enemy_description": self.enemy.description if self.enemy else None,
            "enemy_max_hp": self.enemy.max_hp if self.enemy else None,
            "enemy_attack": self.enemy.attack if self.enemy else None,
            "enemy_reward_xp": self.enemy.reward_xp if self.enemy else None,
            "enemy": enemy_data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], room_id: Optional[str] = None) -> "RoomSnapshot":
        item_data_list = data.get("item_details") or data.get("items") or []
        items = []
        for item_data in item_data_list:
            if isinstance(item_data, dict):
                items.append(ItemSnapshot.from_dict(item_data))
            else:
                items.append(ItemSnapshot(name=str(item_data), description=""))

        enemy_data = data.get("enemy")
        if isinstance(enemy_data, dict):
            enemy = EnemySnapshot.from_dict(enemy_data)
        elif data.get("enemy_name"):
            enemy = EnemySnapshot(
                name=data["enemy_name"],
                description=data.get("enemy_description", ""),
                hp=data.get("enemy_hp", 0),
                max_hp=data.get("enemy_max_hp", data.get("enemy_hp", 0)),
                attack=data.get("enemy_attack", 0),
                reward_xp=data.get("enemy_reward_xp", 10),
            )
            if data.get("enemy_alive") is False:
                enemy.hp = 0
        else:
            enemy = None

        snapshot_id = data.get("id", room_id)
        if not snapshot_id:
            raise ValueError("房间快照缺少 id")

        return cls(
            id=snapshot_id,
            name=data.get("name", snapshot_id),
            description=data.get("description", ""),
            exits=dict(data.get("exits", {})),
            items=items,
            enemy=enemy,
            is_boss_room=data.get("is_boss_room", False),
            has_looked=data.get("has_looked", False),
            last_room=data.get("last_room", ""),
        )


@dataclass
class GameSnapshot:
    player: PlayerSnapshot
    rooms: Dict[str, RoomSnapshot] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "player": self.player.to_dict(),
            "meta": dict(self.meta),
            "rooms": {room_id: room_snapshot.to_dict() for room_id, room_snapshot in self.rooms.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameSnapshot":
        player_data = data["player"]
        player = PlayerSnapshot.from_dict(player_data)

        rooms_data = data.get("rooms", {})
        if not isinstance(rooms_data, dict):
            raise ValueError("rooms 节点格式不正确")

        rooms: Dict[str, RoomSnapshot] = {}
        for room_id, room_data in rooms_data.items():
            if not isinstance(room_data, dict):
                raise ValueError(f"房间 {room_id} 快照格式不正确")
            rooms[room_id] = RoomSnapshot.from_dict(room_data, room_id=room_id)

        meta = data.get("meta", {})
        if not isinstance(meta, dict):
            raise ValueError("meta 节点格式不正确")

        return cls(player=player, rooms=rooms, meta=meta)