import unittest

from backend.models import PreferenceInput
from backend.services.key_service import is_reasonable_api_key, mask_api_key
from backend.services.prompt_service import build_recommend_prompt
from backend.services.recommend_service import parse_ai_recommendations


class Member4ServiceTests(unittest.TestCase):
    def test_mask_api_key(self):
        self.assertEqual(mask_api_key("sk-1234567890abcd"), "sk-****abcd")
        self.assertEqual(mask_api_key("short"), "*****")

    def test_key_validation(self):
        self.assertTrue(is_reasonable_api_key("sk-valid-key-123"))
        self.assertFalse(is_reasonable_api_key("too-short"))
        self.assertFalse(is_reasonable_api_key("sk invalid key"))

    def test_prompt_contains_json_schema(self):
        prompt = build_recommend_prompt(
            PreferenceInput(genres=["动作"], platforms=["PC"]),
            [],
            3,
        )
        self.assertIn("用户偏好 JSON", prompt)
        self.assertIn("recommendations", prompt)

    def test_parse_ai_recommendations(self):
        raw = """```json
        {"recommendations":[{"title":"哈迪斯","reason":"匹配动作偏好","suitable_for":"单人玩家","platforms":["PC"],"tags":["动作"],"match_score":92}]}
        ```"""
        items = parse_ai_recommendations(raw, 5)
        self.assertEqual(items[0].title, "哈迪斯")
        self.assertEqual(items[0].match_score, 92)


if __name__ == "__main__":
    unittest.main()

