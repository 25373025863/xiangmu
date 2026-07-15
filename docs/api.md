# API 接口

统一后端地址：`http://127.0.0.1:8000`。除 FastAPI 自动生成的错误外，成功响应统一包含 `success`、`message`、`data` 和 `timestamp`。

| 方法 | 路径 | 状态 | 说明 |
| --- | --- | --- | --- |
| GET | `/api/health` | 已完成 | 健康检查与版本信息 |
| POST | `/api/preferences/submit` | 已完成 | 校验并规范化用户偏好 |
| POST | `/api/steam/profile` | 已完成 | 读取 Steam 公开资料；游戏库优先使用服务器 `STEAM_API_KEY` 调用官方 API，旧公开 XML 仅作兼容回退 |
| GET | `/api/catalogue/games` | 已完成 | 首页使用的 Steam 在线游戏目录；支持搜索、排序、分页、自动封面与本地降级 |
| GET | `/api/games` | 已完成 | 按关键词、类型、平台和标签查询游戏 |
| GET | `/api/games/{game_id}` | 已完成 | 使用统一游戏 ID 查询详情 |
| POST | `/api/key/check` | 已完成 | 检查并规范化会话级 Key、接口地址和模型；不持久化明文 Key |
| POST | `/api/recommend` | 已完成 | AI 推荐；支持逐请求 Provider 配置，无 Key 时可使用本地演示算法 |
| GET | `/api/config/check` | 已完成 | 检查非敏感运行配置 |
| GET/POST/DELETE | `/api/favorites` | 已完成 | 收藏的新增、分页查询和删除 |
| GET | `/api/histories` | 已完成 | 推荐历史分页查询；每次推荐成功后自动保存 |

完整请求模型和交互调试页面见 `/docs`。

## AI Provider 会话配置

设置页只把用户配置保存在当前浏览器 `sessionStorage`。Key 在检查和推荐请求中均通过 `x-ai-api-key` 请求头传递；接口地址和模型为非敏感字段，使用 JSON 请求体传递。

`POST /api/key/check` 请求体：

```json
{
  "apiBaseUrl": "https://api.example.com/v1",
  "model": "provider-model"
}
```

服务端会把以 `/v1` 结尾的地址规范化为 `/v1/chat/completions`。公网地址必须使用 HTTPS；`localhost`、`127.0.0.1` 和 `::1` 可使用 HTTP。该接口只检查格式和使用策略，不会请求上游验证账户、余额或模型权限。

成功响应只返回脱敏 Key、规范化后的 `apiBaseUrl`、`model` 和实际配置来源。自定义接口或模型必须同时提供有效格式的用户 Key；未提供用户 Key 时，后端默认 Key 只会使用后端 `.env` 中的默认接口和模型。

`POST /api/recommend` 使用相同的 `x-ai-api-key` 请求头，并可在原请求体中增加：

```json
{
  "apiBaseUrl": "https://api.example.com/v1/chat/completions",
  "model": "provider-model"
}
```

## 首页在线游戏目录

`GET /api/catalogue/games` 由主后端联网读取 Steam Store 搜索结果，首页使用该接口进行卡片式无限加载。它与本地推荐候选接口 `/api/games` 分离，不受本地演示数据数量限制。

查询参数：

| 参数 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- |
| `keyword` | 空字符串 | 最长 100 个字符 | 按 Steam 搜索词查询游戏；服务端会去除首尾空白 |
| `page` | `1` | 大于或等于 `1` | 逻辑页码 |
| `size` | `12` | `1` 至 `25` | 每页卡片数；服务端会跨 Steam 固定 25 条数据块正确切片 |
| `sort` | `topsellers` | `topsellers`、`released`、`price`、`name` | 分别表示畅销优先、最新发布、价格从低到高和名称排序 |

成功响应仍使用统一的 `success` 包装，目录数据位于 `data`：

```json
{
  "success": true,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "steam-1172470",
        "steam_app_id": 1172470,
        "title": "Apex Legends",
        "cover_url": "https://shared.fastly.steamstatic.com/...jpg",
        "store_url": "https://store.steampowered.com/app/1172470/...",
        "platforms": ["Windows"],
        "release_date": "2020 年 11 月 4 日",
        "review_score": 44,
        "review_label": "褒贬不一",
        "price": "免费",
        "source": "steam"
      }
    ],
    "total": 6250,
    "page": 1,
    "size": 12,
    "has_more": true,
    "source": "steam",
    "degraded": false
  },
  "timestamp": "2026-07-15T00:00:00+00:00"
}
```

卡片字段说明：

| 字段 | 说明 |
| --- | --- |
| `id` | 在线条目使用 `steam-{appid}` 格式；本地降级条目保留本地统一 ID |
| `steam_app_id` | Steam App ID；非 Steam 本地游戏可为 `null` |
| `title` | 游戏名称 |
| `cover_url` | Steam 商店封面 URL；本地无已知封面时为空字符串 |
| `store_url` | Steam 商店详情链接；本地非 Steam 游戏可为空字符串 |
| `platforms` | Steam 标注的支持平台列表 |
| `release_date` | 商店展示的发行日期，缺失时为空字符串 |
| `review_score` | 用户好评百分比，缺失时为 `null` |
| `review_label` | 商店评测摘要，例如“特别好评” |
| `price` | 最终展示价格或“免费” |
| `source` | 单个条目的来源，当前为 `steam` 或 `local` |

Steam Store 超时、返回无效状态或页面结构暂时无法解析时，接口不会直接返回 `500`，而是分页返回当前本地游戏数据。此时 `data.source` 为 `local`、`data.degraded` 为 `true`，并包含面向用户的 `data.fallback_message`。前端应展示该提示，不应把降级数据的数量解释为完整在线目录总量。

## Steam 游戏库读取

`POST /api/steam/profile` 接受 `SteamID64`、`STEAM_X:Y:Z`、`[U:1:accountId]`、`/profiles/<SteamID64>`、`/id/<自定义 ID>`，以及这些个人资料页的子页面链接。

Steam Community 的旧游戏库 XML 入口会对部分公开账号重定向至登录页，因此生产环境应在后端 `.env` 配置 `STEAM_API_KEY`。接口会优先通过 Steam Web API 获取已拥有游戏和最近游玩；没有 Key 或 Steam 未公开“游戏详情”时，仍返回可用的个人资料摘要，并以 `data_source: "profile_only"` 和明确的 `message` 提示原因。前端应保留手动偏好输入作为回退，不应把零游戏数误认为导入成功。
