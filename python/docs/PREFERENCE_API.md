# 用户偏好与 Steam 接口

服务启动后，页面位于 `/`，接口文档位于 `/docs`。所有请求均使用 `Content-Type: application/json`。

## 1. 读取 Steam 公开资料

`POST /api/steam/profile`

```json
{"steam_identifier": "https://steamcommunity.com/id/example"}
```

`steam_identifier` 支持 SteamID、17 位 SteamID64、`STEAM_X:Y:Z`、`steamcommunity.com/profiles/...` 链接、`steamcommunity.com/id/...` 链接或自定义 URL 名称。

接口不会要求用户输入 Steam 密码、Cookie 或 API Key。后端配置了 `STEAM_API_KEY` 时，会优先调用官方 Steam Web API 获取已拥有游戏和最近游玩记录；未配置时，自动降级读取 Steam Community 公开 XML。

| 值 | 含义 |
| --- | --- |
| `public` | 成功获取公开资料，`inferred_game_types`、`top_games` 可用于预填表单 |
| `private` | 资料或游戏库不可见 |
| `not_found` | Steam 标识不存在 |
| `unavailable` | 网络、Steam 限流或上游暂时不可用 |

成功响应核心字段：

```json
{
  "steam_id64": "7656119...",
  "visibility": "public",
  "game_count": 42,
  "total_playtime_hours": 380.5,
  "top_games": [{"name": "Example", "hours_played": 20.5}],
  "recent_games": [{"app_id": 123, "name": "Example", "hours_played": 3.2}],
  "owned_game_app_ids": [123, 456],
  "inferred_game_types": ["动作", "RPG"],
  "suggested_player_mode": "单人",
  "suggested_platforms": ["PC"],
  "data_source": "steam_web_api"
}
```

`owned_game_app_ids` 是推荐模块用于排除用户已拥有游戏的完整应用 ID 列表；`top_games`、`recent_games` 仅保留最多 5 项供展示和 prompt 使用。`data_source` 为 `steam_web_api`、`public_xml` 或 `profile_only`。公开 XML 不保证提供最近游玩或类型数据，因此摘要是辅助推荐信号，用户仍可在页面中修改。资料私密、不可访问或读取失败时，页面会保留手动填写流程。

## 2. 提交推荐偏好

`POST /api/preferences/submit`

```json
{
  "platforms": ["PC", "Switch"],
  "game_types": ["动作", "RPG"],
  "player_mode": "单人",
  "art_styles": ["写实"],
  "duration_preference": "适中(10-30h)",
  "budget": "100元内",
  "chinese_required": true,
  "notes": "希望有合作内容",
  "steam_summary": null
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `platforms` | 是 | 非空且不重复：`PC`、`Switch`、`PS5`、`Xbox`、`手机` |
| `game_types` | 是 | 非空且不重复：动作、RPG、射击、策略、模拟经营、休闲、独立游戏 |
| `player_mode` | 否 | 单人、本地多人、在线多人、MMO；默认单人 |
| `art_styles` | 否 | 最多 8 项，用于额外筛选 |
| `duration_preference` | 否 | 短平快(&lt;10h)、适中(10-30h)、杀时间(30h+)、无限游玩 |
| `budget` | 否 | 免费、100元内、100-300元、300元以上 |
| `chinese_required` | 否 | 是否只推荐支持中文的游戏，默认 `false` |
| `notes` | 否 | 最长 1000 字符，首尾空白会移除 |
| `steam_summary` | 否 | 直接携带 `/api/steam/profile` 返回的公开摘要；推荐模块可将其作为历史偏好信号 |

非法枚举、空的必填数组、重复选项和超长内容均返回 HTTP `422`。成功时 `data` 是已校验、可直接传给后续推荐模块的标准格式。
