# 游戏数据接口约定

本模块的 Python 后端默认运行在 `http://127.0.0.1:8000`，前端页面通过同源接口请求游戏数据。

| 功能 | 请求方法 | 接口路径 | 说明 |
| --- | --- | --- | --- |
| 健康检查 | `GET` | `/api/health` | 检查本地服务是否正常运行 |
| 游戏列表 | `GET` | `/api/games` | 获取游戏数据，支持筛选 |
| 游戏详情 | `GET` | `/api/games/:id` | 按游戏 ID 查询完整数据 |

## 列表查询参数

```text
GET /api/games?keyword=动作&genre=动作角色扮演&platform=电脑&tag=科幻
```

| 参数 | 示例 | 说明 |
| --- | --- | --- |
| `keyword` | `动作` | 搜索游戏名称、标签或简介 |
| `genre` | `动作角色扮演` | 精确匹配游戏类型 |
| `platform` | `电脑` | 精确匹配游戏平台 |
| `tag` | `科幻` | 精确匹配游戏标签 |

## 统一返回格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0
  }
}
```

## 游戏对象字段

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
  "description": "游戏简介"
}
```

`review_distribution` 的 `good`、`medium`、`poor` 分别表示好评、中等、差评百分比，三个值合计应为 `100`。前端未选择游戏时使用总体评分分组；选择单个游戏后，环图使用该字段显示评分系统。
