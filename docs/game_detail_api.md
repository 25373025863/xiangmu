# 游戏详情模块

## 接口

`GET /api/games/{game_id}` 按稳定游戏 ID 返回详情。

成功响应：

```json
{
  "success": true,
  "data": {
    "id": "g003",
    "title": "哈迪斯",
    "cover": "https://...",
    "genres": ["动作", "Roguelike"],
    "platforms": ["PC", "Switch"],
    "tags": ["单人", "快节奏"],
    "price": "约 80 元",
    "score": 9.3,
    "developer": "Supergiant Games",
    "release_date": "2020-09-17",
    "description": "...",
    "suitable_for": ["喜欢快节奏动作战斗的玩家"],
    "purchase_url": "https://..."
  }
}
```

未知 ID 返回 HTTP 404：

```json
{ "detail": "游戏不存在" }
```

## 前端跳转

推荐卡片必须携带 `game_id`（或与游戏数据一致的 `id`）。`GameCard.vue` 会跳转到：

```text
/games/{gameId}?reason={推荐理由}
```

推荐理由同时保存到 `sessionStorage`，刷新详情页后仍可显示；游戏基础信息始终通过详情接口重新加载。
