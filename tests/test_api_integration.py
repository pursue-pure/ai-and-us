"""REST API 集成测试，覆盖 Web 前端的核心通信链路。"""
import pytest
from fastapi.testclient import TestClient

from game.api import _sessions, app


@pytest.fixture(autouse=True)
def clear_sessions():
    _sessions.clear()
    yield
    _sessions.clear()


@pytest.fixture
def client():
    return TestClient(app)


def create_session(client):
    response = client.post("/session", json={"player_name": "集成测试玩家"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["session_id"].startswith("sess-")
    return payload


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_session_state_move_look_and_take_item(client):
    payload = create_session(client)
    session_id = payload["session_id"]

    move_response = client.post(f"/session/{session_id}/move", json={"direction": "north"})
    assert move_response.status_code == 200
    moved = move_response.json()
    assert moved["room"]["id"] == "hall"
    assert moved["player"]["current_room"] == "hall"

    look_response = client.post(f"/session/{session_id}/look")
    assert look_response.status_code == 200
    looked = look_response.json()
    assert looked["room"]["has_looked"] is True
    assert looked["room"]["items"][0]["name"] == "生命药水"

    take_response = client.post(f"/session/{session_id}/inventory/take", json={"item_name": "生命药水"})
    assert take_response.status_code == 200
    taken = take_response.json()
    assert any(item["name"] == "生命药水" for item in taken["player"]["inventory"])
    assert taken["room"]["items"] == []


def test_combat_endpoint_updates_player_and_enemy_state(client):
    payload = create_session(client)
    session_id = payload["session_id"]

    client.post(f"/session/{session_id}/move", json={"direction": "north"})
    client.post(f"/session/{session_id}/move", json={"direction": "east"})

    attack_response = client.post(f"/session/{session_id}/attack")
    assert attack_response.status_code == 200
    attacked = attack_response.json()

    assert "攻击" in attacked["message"]
    assert attacked["room"]["enemy"]["hp"] == 10
    assert attacked["player"]["hp"] == 45


def test_command_endpoint_reuses_existing_command_parser(client):
    payload = create_session(client)
    session_id = payload["session_id"]

    response = client.post(f"/session/{session_id}/command", json={"command": "look"})

    assert response.status_code == 200
    assert response.json()["room"]["has_looked"] is True


def test_missing_session_returns_404(client):
    response = client.get("/session/sess-missing")

    assert response.status_code == 404
    assert "不存在" in response.json()["detail"]
