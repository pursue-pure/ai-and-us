"""MUD 游戏核心引擎"""
from typing import Dict, Optional

from .infrastructure.json_save_repository import JsonSaveRepository, SaveLoadError
from .models import Enemy, Item, Player, Room
from .services.checkpoint_service import CheckpointService
from .services.combat_service import CombatService
from .snapshot import EnemySnapshot, GameSnapshot, ItemSnapshot, PlayerSnapshot, RoomSnapshot


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
        self._checkpoint_service = CheckpointService()
        self._combat_service = CombatService()
        self._save_repository = JsonSaveRepository()

    @property
    def checkpoint_room_id(self) -> str:
        return self._checkpoint_service.checkpoint_room_id

    @checkpoint_room_id.setter
    def checkpoint_room_id(self, value: str) -> None:
        self._checkpoint_service.checkpoint_room_id = value

    @property
    def checkpoint_time(self) -> str:
        return self._checkpoint_service.checkpoint_time

    @checkpoint_time.setter
    def checkpoint_time(self, value: str) -> None:
        self._checkpoint_service.checkpoint_time = value

    @property
    def last_death_time(self) -> str:
        return self._checkpoint_service.last_death_time

    @last_death_time.setter
    def last_death_time(self, value: str) -> None:
        self._checkpoint_service.last_death_time = value

    @property
    def last_respawn_time(self) -> str:
        return self._checkpoint_service.last_respawn_time

    @last_respawn_time.setter
    def last_respawn_time(self, value: str) -> None:
        self._checkpoint_service.last_respawn_time = value

    def update_checkpoint(self, room_id: Optional[str] = None) -> None:
        """更新检查点（固定地点 + 固定时间）。"""
        self._checkpoint_service.update_checkpoint(self.player, self.rooms, room_id)

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
        """攻击敌人 — 委托 CombatService 执行，返回格式化文本。"""
        if not self.player:
            return "游戏未开始。"
        if not self.player.is_alive:
            return "你已经死了，无法攻击。"
        room = self.get_current_room()
        if not room or not room.enemy or not room.enemy.is_alive():
            return "这里没有敌人。"

        combat_result = self._combat_service.attack(self.player, room)

        if combat_result.player_dead:
            self._checkpoint_service.mark_death()
        if combat_result.boss_victory:
            self.game_won = True

        return "\n".join(combat_result.messages)

    def _build_item_snapshot(self, item: Item) -> ItemSnapshot:
        return ItemSnapshot(
            name=item.name,
            description=item.description,
            item_type=item.item_type,
            effect=item.effect,
        )

    def _build_enemy_snapshot(self, enemy: Enemy) -> EnemySnapshot:
        return EnemySnapshot(
            name=enemy.name,
            description=enemy.description,
            hp=enemy.hp,
            max_hp=enemy.max_hp,
            attack=enemy.attack,
            reward_xp=enemy.reward_xp,
        )

    def _build_room_snapshot(self, room: Room) -> RoomSnapshot:
        return RoomSnapshot(
            id=room.id,
            name=room.name,
            description=room.description,
            exits=dict(room.exits),
            items=[self._build_item_snapshot(item) for item in room.items],
            enemy=self._build_enemy_snapshot(room.enemy) if room.enemy else None,
            is_boss_room=room.is_boss_room,
            has_looked=room.has_looked,
            last_room=room.last_room,
        )

    def _build_player_snapshot(self) -> PlayerSnapshot:
        if not self.player:
            raise ValueError("游戏未开始。")

        return PlayerSnapshot(
            name=self.player.name,
            current_room=self.player.current_room,
            last_room=self.player.last_room,
            hp=self.player.hp,
            max_hp=self.player.max_hp,
            attack=self.player.attack,
            inventory=[self._build_item_snapshot(item) for item in self.player.inventory],
            xp=self.player.xp,
            level=self.player.level,
            is_alive=self.player.is_alive,
        )

    def _build_snapshot(self) -> GameSnapshot:
        if not self.player:
            raise ValueError("游戏未开始。")

        return GameSnapshot(
            player=self._build_player_snapshot(),
            rooms={room_id: self._build_room_snapshot(room) for room_id, room in self.rooms.items()},
            meta=self._checkpoint_service.to_meta(),
        )

    def _restore_room(self, snapshot: RoomSnapshot) -> Room:
        enemy = None
        if snapshot.enemy:
            enemy = Enemy(
                name=snapshot.enemy.name,
                description=snapshot.enemy.description,
                hp=snapshot.enemy.hp,
                max_hp=snapshot.enemy.max_hp,
                attack=snapshot.enemy.attack,
                reward_xp=snapshot.enemy.reward_xp,
            )

        return Room(
            id=snapshot.id,
            name=snapshot.name,
            description=snapshot.description,
            exits=dict(snapshot.exits),
            items=[Item(item.name, item.description, item.item_type, item.effect) for item in snapshot.items],
            enemy=enemy,
            is_boss_room=snapshot.is_boss_room,
            has_looked=snapshot.has_looked,
            last_room=snapshot.last_room,
        )

    def _apply_snapshot(self, snapshot: GameSnapshot) -> None:
        self.rooms = {room_id: self._restore_room(room_snapshot) for room_id, room_snapshot in snapshot.rooms.items()}

        player_snapshot = snapshot.player
        self.player = Player(
            name=player_snapshot.name,
            current_room=player_snapshot.current_room,
            last_room=player_snapshot.last_room,
            hp=player_snapshot.hp,
            max_hp=player_snapshot.max_hp,
            attack=player_snapshot.attack,
            inventory=[Item(item.name, item.description, item.item_type, item.effect) for item in player_snapshot.inventory],
            xp=player_snapshot.xp,
            level=player_snapshot.level,
            is_alive=player_snapshot.is_alive,
        )

        self._checkpoint_service.apply_meta(snapshot.meta, self.rooms, self.player)

    def respawn(self) -> str:
        """复活"""
        if not self.player:
            return "游戏未开始。"

        if self.player.is_alive:
            return "你还活着，不需要复活。"

        respawn_result = self._checkpoint_service.respawn(self.player, self.rooms)
        if not respawn_result.success:
            return f"❌ 复活失败：{respawn_result.error}"

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
        if not self.player:
            return "游戏未开始。"

        # 每次手动保存都更新检查点位置和时间
        self.update_checkpoint()

        try:
            self._save_repository.save(filename, self._build_snapshot())
        except (OSError, ValueError, SaveLoadError) as exc:
            return f"❌ 保存失败：{exc}"

        return f"💾 游戏已保存到 {filename}"

    def load_game(self, filename: str) -> str:
        """加载游戏"""
        try:
            snapshot = self._save_repository.load(filename)
            self._apply_snapshot(snapshot)

            return f"💾 游戏已从 {filename} 加载。欢迎回来，{self.player.name}！"
        except SaveLoadError as exc:
            return f"❌ 加载失败：{exc}"
