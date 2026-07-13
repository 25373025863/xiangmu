from fastapi.testclient import TestClient

from game_detail_module.app import app

client = TestClient(app)


def test_get_game_detail() -> None:
    response = client.get("/api/games/g003")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["id"] == "g003"
    assert body["data"]["title"] == "哈迪斯"


def test_get_game_detail_returns_404_for_unknown_id() -> None:
    response = client.get("/api/games/missing-game")

    assert response.status_code == 404
    assert response.json()["detail"] == "游戏不存在"


def test_game_detail_page_is_served() -> None:
    response = client.get("/games/g003")

    assert response.status_code == 200
    assert "游戏详情" in response.text
