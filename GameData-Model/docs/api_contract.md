# 游戏数据接口约定

本模块的 Python 后端默认运行在 `http://127.0.0.1:18800`，与项目主后端的 `8000` 端口分离。目录页面通过同源接口分页获取游戏数据，因此首屏内容不依赖第三方图表或封面服务。

| 功能 | 请求方法 | 接口路径 | 说明 |
| --- | --- | --- | --- |
| 健康检查 | `GET` | `/api/health` | 检查本地服务是否正常运行 |
| 筛选项 | `GET` | `/api/games/options` | 获取类型、平台、标签选项 |
| 游戏列表 | `GET` | `/api/games` | 分页获取游戏数据，支持筛选和排序 |
| 游戏详情 | `GET` | `/api/games/:id` | 按游戏 ID 查询完整数据 |
| 本地封面回退 | `GET` | `/api/games/:id/cover.svg` | 无网络或无 Steam 条目时的 SVG 封面 |

## 列表查询参数

```text
GET /api/games?keyword=动作&genre=动作角色扮演&platform=电脑&tag=科幻&page=1&size=12&sort=rating
```

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| `keyword` | `动作` | 搜索游戏名称、标签或简介 |
| `genre` | `动作角色扮演` | 精确匹配游戏类型 |
| `platform` | `电脑` | 精确匹配游戏平台 |
| `tag` | `科幻` | 精确匹配游戏标签 |
| `page` | `1` | 从 `1` 开始的页码，默认为 `1` |
| `size` | `12` | 每页数量，默认 `12`，最大 `48` |
| `sort` | `rating` | `rating`、`release_desc`、`price_asc` 或 `name` |

## 统一返回格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 60,
    "page": 1,
    "size": 12,
    "total_pages": 5,
    "has_more": true
  }
}
```

`items` 中保留原有游戏字段，并新增 `cover`：

```json
{
  "id": "game-001",
  "name": "星露谷物语",
  "platforms": ["电脑", "任天堂掌机"],
  "genre": "模拟经营",
  "price": 48.0,
  "rating": 9.3,
  "review_distribution": {"good": 95, "medium": 4, "poor": 1},
  "tags": ["休闲", "种田"],
  "release_date": "2016-02-26",
  "developer": "关心猿",
  "description": "游戏简介",
  "cover": {
    "url": "https://cdn.cloudflare.steamstatic.com/steam/apps/413150/header.jpg",
    "fallback_url": "/api/games/game-001/cover.svg",
    "source": "steam",
    "steam_app_id": 413150
  }
}
```

`cover.url` 仅在已知 Steam App ID 时提供。前端会先显示 `fallback_url`，在 Steam 封面成功载入后再替换，因此断网、跨域阻断或非 Steam 游戏不会显示破损图片。

`review_distribution` 的 `good`、`medium`、`poor` 分别表示好评、中等、差评百分比，三个值合计应为 `100`。
