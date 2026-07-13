# 游戏详情模块

## 文件对应

- 前端详情页：`frontend/src/pages/GameDetailPage.js`
- 推荐卡片跳转：`frontend/src/components/GameCard.js`
- 前端请求：`frontend/src/api/gameApi.js`
- 后端路由：`backend/src/routes/gameRoutes.js`
- 后端控制器：`backend/src/controllers/gameController.js`
- 后端服务与数据：`backend/src/services/gameService.js`、`backend/src/data/games.json`

## 接口

`GET /api/games/:id` 按稳定游戏 ID 返回详情。

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "g003",
    "title": "哈迪斯",
    "cover": "https://...",
    "platforms": ["PC", "Switch"],
    "genres": ["动作", "Roguelike"],
    "tags": ["单人", "快节奏"],
    "description": "...",
    "suitableFor": ["喜欢快节奏动作战斗的玩家"],
    "purchaseUrl": "https://..."
  }
}
```

找不到游戏时返回 HTTP 404：

```json
{ "code": "GAME_NOT_FOUND", "message": "游戏不存在", "data": null }
```

## 接入

在 `backend/src/app.js` 中注册路由：

```js
const gameRoutes = require('./routes/gameRoutes')
app.use('/api/games', gameRoutes)
```

在前端路由中注册页面：

```jsx
<Route path="/games/:gameId" element={<GameDetailPage />} />
```

`GameCard.js` 会将推荐结果的 `gameId`（兼容 `game_id`、`id`）和本次推荐理由传入详情页。推荐理由保存于 `sessionStorage`，基础游戏资料始终从详情接口读取。

## 本地运行与验证

```powershell
cd backend
npm install
npm test
npm run dev
```

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

开发环境下，Vite 将 `/api` 请求代理到 `http://127.0.0.1:3000`。访问 `/games/g003` 可查看详情页。
