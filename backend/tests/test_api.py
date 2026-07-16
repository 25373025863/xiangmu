import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.src.app import app
from backend.src.config.settings import get_settings


class UnifiedApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)
        data_dir = Path(self._temporary_directory.name)
        settings = replace(get_settings(), data_dir=data_dir)
        for service_module in (
            "backend.src.services.favorite_service.get_settings",
            "backend.src.services.history_service.get_settings",
        ):
            settings_patch = patch(service_module, return_value=settings)
            settings_patch.start()
            self.addCleanup(settings_patch.stop)

    def test_health_uses_standard_response(self) -> None:
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])

    def test_games_and_detail_use_same_id(self) -> None:
        games = self.client.get("/api/games").json()["data"]["items"]
        self.assertTrue(games)
        game_id = games[0]["id"]
        detail = self.client.get(f"/api/games/{game_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["id"], game_id)

    def test_demo_recommendation_uses_canonical_games_and_records_history(self) -> None:
        with patch(
            "backend.src.services.recommend_service.catalogue_service.list_games",
            return_value={"source": "local", "degraded": True, "items": []},
        ):
            response = self.client.post(
                "/api/recommend",
                json={
                    "preferences": {"genres": ["动作"], "platforms": ["PC"]},
                    "limit": 3,
                },
            )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["data"]), 3)
        self.assertEqual(payload["meta"]["returned_count"], 3)
        history = self.client.get("/api/histories")
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()["data"]["total"], 1)

    def test_favorite_create_list_and_delete(self) -> None:
        created = self.client.post("/api/favorites", json={"game_id": "g003"})
        self.assertEqual(created.status_code, 201)
        self.assertTrue(created.json()["created"])
        listed = self.client.get("/api/favorites")
        self.assertEqual(listed.json()["data"]["total"], 1)
        deleted = self.client.delete("/api/favorites/g003")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(self.client.get("/api/favorites").json()["data"]["total"], 0)


if __name__ == "__main__":
    unittest.main()
