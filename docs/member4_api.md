# 成员4：AI 推荐模块说明

## 文件范围

- `backend/src/routes/key_routes.py`：`/api/key/check` 路由
- `backend/src/services/key_service.py`：Key 脱敏、接口与模型校验、逐请求 Provider 选择
- `backend/src/services/ai_service.py`：OpenAI 兼容 Chat Completions 调用
- `backend/src/services/recommend_service.py`：推荐生成、AI JSON 解析、本地演示兜底
- `frontend/src/pages/SettingsPage.js`：正式设置页
- `frontend/src/utils/providerConfig.js`：会话配置的统一读取、迁移和清除

## 运行方式

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m backend.src.server
```

打开 `http://127.0.0.1:5173/settings` 设置用户 Key、接口地址和模型；接口调试页面位于 `http://127.0.0.1:8000/docs`。

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

Key 使用请求头：

```text
x-ai-api-key: user_api_key_here
```

请求体只包含非敏感字段：

```json
{
  "apiBaseUrl": "https://api.example.com/v1",
  "model": "provider-model"
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
    "activeSource": "user",
    "apiBaseUrl": "https://api.example.com/v1/chat/completions",
    "model": "provider-model"
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
  "apiBaseUrl": "https://api.example.com/v1/chat/completions",
  "model": "provider-model",
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

