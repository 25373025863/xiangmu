from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_get_game_detail() -> None:
    response = client.get("/api/games/g003")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == "g003"
    assert body["data"]["title"] == "哈迪斯"
    assert body["data"]["cover"]


def test_game_detail_returns_404_for_unknown_id() -> None:
    response = client.get("/api/games/not-a-game")

    assert response.status_code == 404
    assert response.json()["detail"] == "游戏不存在"
