"""REST API 适配层，将 Web 前端接入既有游戏引擎。"""
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .commands import CommandHandler
from .engine import GameEngine
from .models import Enemy, Item
from .world import create_demo_world


WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(
    title="MUD 洞穴探险游戏 API",
    description="命令行 MUD 游戏的 RESTful 后端，供 2D Web 图形界面调用。",
    version="2.0.0",
)


class SessionContext(BaseModel):
    engine: Any
    handler: Any

    class Config:
        arbitrary_types_allowed = True


class CreateSessionRequest(BaseModel):
    player_name: str = Field(default="冒险者", min_length=1, max_length=24)


class MoveRequest(BaseModel):
    direction: str = Field(..., min_length=1)


class ItemRequest(BaseModel):
    item_name: str = Field(..., min_length=1)


class SaveLoadRequest(BaseModel):
    filename: str = Field(default="savegame.json", min_length=1)


class CommandRequest(BaseModel):
    command: str = Field(..., min_length=1)


_sessions: dict[str, SessionContext] = {}


def _item_payload(item: Item) -> dict:
    return {
        "name": item.name,
        "description": item.description,
        "type": item.item_type,
        "effect": item.effect,
    }


def _enemy_payload(enemy: Enemy | None) -> dict | None:
    if not enemy:
        return None
    return {
        "name": enemy.name,
        "description": enemy.description,
        "hp": enemy.hp,
        "max_hp": enemy.max_hp,
        "attack": enemy.attack,
        "reward_xp": enemy.reward_xp,
        "alive": enemy.is_alive(),
    }


def _player_payload(engine: GameEngine) -> dict:
    player = engine.player
    if not player:
        return {}
    return {
        "name": player.name,
        "current_room": player.current_room,
        "last_room": player.last_room,
        "hp": player.hp,
        "max_hp": player.max_hp,
        "base_attack": player.attack,
        "attack": player.get_attack_power(),
        "xp": player.xp,
        "level": player.level,
        "alive": player.is_alive,
        "inventory": [_item_payload(item) for item in player.inventory],
    }


def _room_payload(engine: GameEngine) -> dict:
    room = engine.get_current_room()
    if not room:
        return {}
    return {
        "id": room.id,
        "name": room.name,
        "description": room.description,
        "exits": dict(room.exits),
        "items": [_item_payload(item) for item in room.items] if room.has_looked else [],
        "has_looked": room.has_looked,
        "enemy": _enemy_payload(room.enemy),
        "is_boss_room": room.is_boss_room,
        "boss_direction": engine.get_boss_direction(),
    }


def _world_payload(engine: GameEngine) -> list[dict]:
    rooms = []
    for room in engine.rooms.values():
        rooms.append(
            {
                "id": room.id,
                "name": room.name,
                "exits": dict(room.exits),
                "visited": bool(room.has_looked) or (engine.player and engine.player.current_room == room.id),
                "has_enemy": bool(room.enemy and room.enemy.is_alive()),
                "is_boss_room": room.is_boss_room,
            }
        )
    return rooms


def _state_payload(session_id: str, engine: GameEngine, message: str = "") -> dict:
    return {
        "session_id": session_id,
        "message": message,
        "player": _player_payload(engine),
        "room": _room_payload(engine),
        "world": _world_payload(engine),
        "game_won": engine.game_won,
        "checkpoint": {
            "room_id": engine.checkpoint_room_id,
            "time": engine.checkpoint_time,
            "last_death_time": engine.last_death_time,
            "last_respawn_time": engine.last_respawn_time,
        },
    }


def _get_session(session_id: str) -> SessionContext:
    context = _sessions.get(session_id)
    if not context:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="游戏会话不存在")
    return context


def _create_session(player_name: str) -> tuple[str, SessionContext]:
    engine = create_demo_world(player_name)
    context = SessionContext(engine=engine, handler=CommandHandler(engine))
    session_id = f"sess-{uuid4().hex[:8]}"
    _sessions[session_id] = context
    return session_id, context


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/session", status_code=status.HTTP_201_CREATED)
def create_session(request: CreateSessionRequest) -> dict:
    session_id, context = _create_session(request.player_name.strip())
    return _state_payload(session_id, context.engine, "游戏开始！输入 look 搜索房间。")


@app.get("/session/{session_id}")
def get_session_state(session_id: str) -> dict:
    context = _get_session(session_id)
    return _state_payload(session_id, context.engine)


@app.delete("/session/{session_id}")
def delete_session(session_id: str) -> dict:
    _get_session(session_id)
    del _sessions[session_id]
    return {"message": "感谢游玩，再见！"}


@app.post("/session/{session_id}/move")
def move_player(session_id: str, request: MoveRequest) -> dict:
    context = _get_session(session_id)
    message = context.engine.move_player(request.direction.strip().lower())
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/look")
def look_room(session_id: str) -> dict:
    context = _get_session(session_id)
    message = context.engine.look()
    return _state_payload(session_id, context.engine, message)


@app.get("/session/{session_id}/inventory")
def get_inventory(session_id: str) -> dict:
    context = _get_session(session_id)
    return {
        "session_id": session_id,
        "message": context.engine.show_inventory(),
        "inventory": _player_payload(context.engine).get("inventory", []),
    }


@app.post("/session/{session_id}/inventory/take")
def take_item(session_id: str, request: ItemRequest) -> dict:
    context = _get_session(session_id)
    message = context.engine.take_item(request.item_name.strip())
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/inventory/use")
def use_item(session_id: str, request: ItemRequest) -> dict:
    context = _get_session(session_id)
    message = context.engine.use_item(request.item_name.strip())
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/attack")
def attack_enemy(session_id: str) -> dict:
    context = _get_session(session_id)
    message = context.engine.attack_enemy()
    return _state_payload(session_id, context.engine, message)


@app.get("/session/{session_id}/stats")
def get_stats(session_id: str) -> dict:
    context = _get_session(session_id)
    return {
        "session_id": session_id,
        "message": context.engine.show_stats(),
        "player": _player_payload(context.engine),
    }


@app.post("/session/{session_id}/respawn")
def respawn(session_id: str) -> dict:
    context = _get_session(session_id)
    message = context.engine.respawn()
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/save")
def save_game(session_id: str, request: SaveLoadRequest) -> dict:
    context = _get_session(session_id)
    message = context.engine.save_game(request.filename)
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/load")
def load_game(session_id: str, request: SaveLoadRequest) -> dict:
    context = _get_session(session_id)
    message = context.engine.load_game(request.filename)
    return _state_payload(session_id, context.engine, message)


@app.post("/session/{session_id}/command")
def run_command(session_id: str, request: CommandRequest) -> dict:
    context = _get_session(session_id)
    message = context.handler.handle(request.command)
    return _state_payload(session_id, context.engine, message)


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", include_in_schema=False)
def web_index() -> FileResponse:
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Web 前端尚未构建")
    return FileResponse(index_path)
