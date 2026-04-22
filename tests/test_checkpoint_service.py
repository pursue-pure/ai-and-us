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
