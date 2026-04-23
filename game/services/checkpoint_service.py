"""检查点与复活服务。"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict

from ..models import Player, Room


@dataclass
class RespawnResult:
    success: bool
    checkpoint_room_id: str = ""
    checkpoint_time: str = ""
    player_hp: int = 0
    player_max_hp: int = 0
    error: str = ""


class CheckpointService:
    """负责检查点记录、死亡记录与复活流程。"""

    def __init__(self) -> None:
        self.checkpoint_room_id: str = ""
        self.checkpoint_time: str = ""
        self.last_death_time: str = ""
        self.last_respawn_time: str = ""

    def _now_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_checkpoint(self, player: Player | None, rooms: Dict[str, Room], room_id: str | None = None) -> None:
        """更新检查点位置与时间。"""
        if room_id and room_id in rooms:
            self.checkpoint_room_id = room_id
        elif player and player.current_room in rooms:
            self.checkpoint_room_id = player.current_room

        self.checkpoint_time = self._now_str()

    def mark_death(self) -> None:
        """记录死亡时间。"""
        self.last_death_time = self._now_str()

    def _resolve_checkpoint_room(self, player: Player | None, rooms: Dict[str, Room]) -> str:
        if self.checkpoint_room_id in rooms:
            return self.checkpoint_room_id
        if "entrance" in rooms:
            return "entrance"
        if player and player.last_room in rooms:
            return player.last_room
        if player and player.current_room in rooms:
            return player.current_room
        if rooms:
            return next(iter(rooms))
        return ""

    def respawn(self, player: Player, rooms: Dict[str, Room]) -> RespawnResult:
        """执行复活并返回结构化结果。"""
        checkpoint_room_id = self._resolve_checkpoint_room(player, rooms)
        if not checkpoint_room_id:
            return RespawnResult(success=False, error="当前没有可用检查点。")

        player.current_room = checkpoint_room_id
        player.hp = player.max_hp // 2
        player.is_alive = True
        self.last_respawn_time = self._now_str()

        return RespawnResult(
            success=True,
            checkpoint_room_id=checkpoint_room_id,
            checkpoint_time=self.checkpoint_time,
            player_hp=player.hp,
            player_max_hp=player.max_hp,
        )

    def to_meta(self) -> dict:
        return {
            "checkpoint_room_id": self.checkpoint_room_id,
            "checkpoint_time": self.checkpoint_time,
            "last_death_time": self.last_death_time,
            "last_respawn_time": self.last_respawn_time,
        }

    def apply_meta(self, meta: dict, rooms: Dict[str, Room], player: Player | None) -> None:
        self.checkpoint_room_id = meta.get("checkpoint_room_id", "")
        if self.checkpoint_room_id not in rooms and player:
            self.checkpoint_room_id = player.current_room

        self.checkpoint_time = meta.get("checkpoint_time", "") or self._now_str()
        self.last_death_time = meta.get("last_death_time", "")
        self.last_respawn_time = meta.get("last_respawn_time", "")
