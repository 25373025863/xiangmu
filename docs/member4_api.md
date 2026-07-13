# 成员4：AI 推荐模块说明

## 文件范围

- `backend/app.py`：FastAPI 入口，包含 `/api/recommend` 和 `/api/key/check`
- `backend/services/key_service.py`：API Key 校验、脱敏和来源选择
- `backend/services/prompt_service.py`：推荐 prompt 模板
- `backend/services/ai_service.py`：OpenAI 兼容 Chat Completions 调用
- `backend/services/recommend_service.py`：推荐生成、AI JSON 解析、本地演示兜底
- `frontend/settings.html`：可选设置页和接口联调页

## 运行方式

```bash
pip install -r requirements.txt
uvicorn backend.app:app --reload
```

打开 `http://127.0.0.1:8000/` 可以测试 API Key 设置和推荐生成。

## 环境变量

复制 `.env.example` 为 `.env` 后配置：

```env
DEFAULT_AI_API_KEY=your_default_api_key_here
ALLOW_USER_API_KEY=true
AI_API_BASE_URL=https://api.openai.com/v1/chat/completions
AI_MODEL=gpt-4o-mini
AI_TIMEOUT_SECONDS=30
DEMO_MODE_WITHOUT_KEY=true
```

`.env` 不能提交到 GitHub。后端不会打印、返回或保存真实 API Key。

## POST `/api/key/check`

请求体：

```json
{
  "apiKey": "user_api_key_here"
}
```

返回示例：

```json
{
  "success": true,
  "data": {
    "allowUserApiKey": true,
    "hasUserKey": true,
    "userKeyValid": true,
    "maskedUserKey": "sk-****abcd",
    "defaultKeyConfigured": false,
    "activeSource": "user"
  }
}
```

## POST `/api/recommend`

支持请求头：

```text
x-ai-api-key: user_api_key_here
```

请求体：

```json
{
  "preferences": {
    "genres": ["动作", "Roguelike"],
    "platforms": ["PC", "Switch"],
    "budget": "200 元以内",
    "player_mode": "单人",
    "art_style": "精致",
    "play_time": "每次 30 分钟",
    "chinese_support": true,
    "extra_requirements": "希望有重复挑战价值"
  },
  "limit": 5
}
```

返回字段：

- `title`：游戏名称
- `reason`：推荐理由
- `suitable_for`：适合的玩家类型
- `platforms`：游戏平台
- `tags`：匹配标签
- `possible_drawbacks`：可能缺点
- `similar_games`：相似游戏
- `match_score`：匹配分数

