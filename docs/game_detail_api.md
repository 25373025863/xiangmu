# 游戏详情模块

## 功能范围

- 从推荐结果跳转至 `/games/{game_id}`。
- 前端详情页请求 `GET /api/games/{game_id}` 并展示封面、标签、平台、简介、适合人群和购买链接。
- 推荐理由通过链接查询参数传递，属于本次推荐，不写入游戏基础数据。

## 接口

```text
GET /api/games/:id
```

成功响应：

```json
{
  "success": true,
  "data": {
    "id": "g003",
    "title": "哈迪斯",
    "cover": "https://...",
    "platforms": ["PC", "Switch"],
    "genres": ["动作", "Roguelike"],
    "tags": ["单人", "快节奏"],
    "description": "...",
    "suitable_for": ["喜欢快节奏动作战斗的玩家"],
    "purchase_url": "https://..."
  }
}
```

未知游戏返回 HTTP 404：

```json
{ "detail": "游戏不存在" }
```

## 文件

- `backend/services/game_service.py`：详情查询和展示字段补充。
- `backend/app.py`：详情 API 与 HTML 页面路由。
- `frontend/game-detail.html`：原生 HTML/CSS/JavaScript 详情页。
- `frontend/settings.html`：推荐结果中的详情跳转入口。
- `tests/test_game_detail.py`：成功、404 和页面路由测试。
