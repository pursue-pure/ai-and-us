"""CheckpointService 单元测试"""

from game.models import Player, Room
from game.services.checkpoint_service import CheckpointService


def test_update_checkpoint_uses_explicit_room_id():
    service = CheckpointService()
    rooms = {
        "room1": Room(id="room1", name="房间1", description=""),
        "room2": Room(id="room2", name="房间2", description=""),
    }
    player = Player(name="测试", current_room="room1")

    service.update_checkpoint(player, rooms, room_id="room2")

    assert service.checkpoint_room_id == "room2"
    assert service.checkpoint_time != ""


def test_update_checkpoint_falls_back_to_player_current_room():
    service = CheckpointService()
    rooms = {
        "room1": Room(id="room1", name="房间1", description=""),
        "room2": Room(id="room2", name="房间2", description=""),
    }
    player = Player(name="测试", current_room="room1")

    service.update_checkpoint(player, rooms, room_id="not_exists")

    assert service.checkpoint_room_id == "room1"
    assert service.checkpoint_time != ""


def test_respawn_success_to_checkpoint_room():
    service = CheckpointService()
    rooms = {
        "room1": Room(id="room1", name="房间1", description=""),
        "room2": Room(id="room2", name="房间2", description=""),
    }
    player = Player(name="测试", current_room="room1", max_hp=80, hp=0, is_alive=False)
    service.update_checkpoint(player, rooms, room_id="room2")

    result = service.respawn(player, rooms)

    assert result.success is True
    assert result.checkpoint_room_id == "room2"
    assert player.current_room == "room2"
    assert player.hp == 40
    assert player.is_alive is True
    assert service.last_respawn_time != ""


def test_respawn_fail_when_no_available_checkpoint():
    service = CheckpointService()
    player = Player(name="测试", current_room="room1", hp=0, is_alive=False)

    result = service.respawn(player, {})

    assert result.success is False
    assert "没有可用检查点" in result.error


def test_respawn_falls_back_to_entrance_when_checkpoint_invalid():
    service = CheckpointService()
    rooms = {
        "entrance": Room(id="entrance", name="入口", description=""),
        "room2": Room(id="room2", name="房间2", description=""),
    }
    player = Player(name="测试", current_room="room2", max_hp=50, hp=0, is_alive=False)
    service.checkpoint_room_id = "missing"

    result = service.respawn(player, rooms)

    assert result.success is True
    assert result.checkpoint_room_id == "entrance"
    assert player.current_room == "entrance"


def test_apply_meta_invalid_checkpoint_falls_back_to_player_room():
    service = CheckpointService()
    rooms = {
        "room1": Room(id="room1", name="房间1", description=""),
        "room2": Room(id="room2", name="房间2", description=""),
    }
    player = Player(name="测试", current_room="room2")
    meta = {
        "checkpoint_room_id": "ghost",
        "checkpoint_time": "",
        "last_death_time": "2026-04-23 10:00:00",
        "last_respawn_time": "2026-04-23 10:01:00",
    }

    service.apply_meta(meta, rooms, player)

    assert service.checkpoint_room_id == "room2"
    assert service.checkpoint_time != ""
    assert service.last_death_time == "2026-04-23 10:00:00"
    assert service.last_respawn_time == "2026-04-23 10:01:00"
