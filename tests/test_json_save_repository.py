"""JSON 存档仓储测试。"""
import json

import pytest

from game.infrastructure.json_save_repository import JsonSaveRepository, SaveLoadError
from game.snapshot import EnemySnapshot, GameSnapshot, ItemSnapshot, PlayerSnapshot, RoomSnapshot


@pytest.fixture
def snapshot() -> GameSnapshot:
    player = PlayerSnapshot(
        name="测试玩家",
        current_room="room1",
        last_room="room0",
        hp=40,
        max_hp=50,
        attack=12,
        inventory=[ItemSnapshot(name="铁剑", description="一把剑", item_type="weapon", effect=8)],
        xp=30,
        level=2,
        is_alive=True,
    )
    rooms = {
        "room1": RoomSnapshot(
            id="room1",
            name="房间 1",
            description="描述 1",
            exits={"north": "room2"},
            items=[ItemSnapshot(name="药水", description="恢复 HP", item_type="potion", effect=25)],
            enemy=EnemySnapshot(name="哥布林", description="", hp=0, max_hp=20, attack=5, reward_xp=30),
            has_looked=True,
        ),
        "room2": RoomSnapshot(
            id="room2",
            name="房间 2",
            description="描述 2",
            exits={"south": "room1"},
        ),
    }
    meta = {
        "checkpoint_room_id": "room1",
        "checkpoint_time": "2026-04-15 10:00:00",
        "last_death_time": "",
        "last_respawn_time": "",
    }
    return GameSnapshot(player=player, rooms=rooms, meta=meta)


def test_save_and_load_round_trip(snapshot, tmp_path):
    repository = JsonSaveRepository()
    save_file = tmp_path / "save.json"

    repository.save(str(save_file), snapshot)
    loaded = repository.load(str(save_file))

    assert loaded.player.name == "测试玩家"
    assert loaded.player.inventory[0].name == "铁剑"
    assert loaded.rooms["room1"].enemy is not None
    assert loaded.rooms["room1"].enemy.hp == 0
    assert loaded.rooms["room1"].items[0].name == "药水"
    assert loaded.meta["checkpoint_room_id"] == "room1"


def test_load_missing_file_raises_saveloaderror(tmp_path):
    repository = JsonSaveRepository()

    with pytest.raises(SaveLoadError) as exc_info:
        repository.load(str(tmp_path / "missing.json"))

    assert "不存在" in str(exc_info.value)


def test_load_corrupt_json_raises_saveloaderror(tmp_path):
    repository = JsonSaveRepository()
    save_file = tmp_path / "broken.json"
    save_file.write_text("{broken json", encoding="utf-8")

    with pytest.raises(SaveLoadError) as exc_info:
        repository.load(str(save_file))

    assert "损坏" in str(exc_info.value)


def test_load_invalid_structure_raises_saveloaderror(tmp_path):
    repository = JsonSaveRepository()
    save_file = tmp_path / "invalid.json"
    save_file.write_text(json.dumps({"player": {}, "rooms": []}, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(SaveLoadError) as exc_info:
        repository.load(str(save_file))

    assert "不正确" in str(exc_info.value)