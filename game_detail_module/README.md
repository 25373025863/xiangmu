# 游戏详情模块

这是独立的 Python/FastAPI + 原生 HTML 模块。除 `game_detail_module/` 自身外，不依赖或改动仓库中的其他成员文件。

## 包含内容

```text
game_detail_module/
├── app.py                 # FastAPI 路由与独立运行入口
├── models.py              # 详情响应模型
├── service.py             # 游戏详情查询
├── data/games.json        # 模块自带演示数据
├── frontend/game-detail.html
├── tests/test_game_detail.py
└── requirements.txt
```

## 单独运行

```powershell
py -m pip install -r game_detail_module/requirements.txt
uvicorn game_detail_module.app:app --reload
```

打开：

```text
http://127.0.0.1:8000/games/g003?reason=匹配动作偏好
```

## 接口

```text
GET /api/games/{game_id}
GET /games/{game_id}
```

未知游戏返回 HTTP 404 和 `{ "detail": "游戏不存在" }`。

## 最终整合

未来主项目需要接入时，在主应用中加入：

```python
from game_detail_module.app import router as game_detail_router

app.include_router(game_detail_router)
```

推荐结果页使用稳定的 `game_id` 跳转：

```text
/games/g003?reason=匹配动作偏好
```
