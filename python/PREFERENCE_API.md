# 用户偏好提交接口

## 请求

- 方法：`POST`
- 地址：`/api/preferences/submit`
- 请求头：`Content-Type: application/json`

```json
{
  "platforms": ["PC", "Switch"],
  "game_types": ["动作", "RPG"],
  "player_mode": "单人",
  "art_styles": ["写实"],
  "duration_preference": "适中(10-30h)",
  "budget": "100元内",
  "chinese_required": true,
  "notes": "希望有合作内容"
}
```

## 参数

| 字段 | 类型 | 必填 | 可用值 / 说明 |
| --- | --- | --- | --- |
| `platforms` | 字符串数组 | 是 | `PC`、`Switch`、`PS5`、`Xbox`、`手机`；至少一项 |
| `game_types` | 字符串数组 | 是 | `动作`、`RPG`、`射击`、`策略`、`模拟经营`、`休闲`、`独立游戏`；至少一项 |
| `player_mode` | 字符串 | 否 | `单人`、`本地多人`、`在线多人`、`MMO`；默认 `单人` |
| `art_styles` | 字符串数组 | 否 | `写实`、`像素`、`二次元`、`卡通渲染` |
| `duration_preference` | 字符串 | 否 | `短平快(<10h)`、`适中(10-30h)`、`杀时间(30h+)`、`无限游玩`；默认 `适中(10-30h)` |
| `budget` | 字符串 | 否 | `免费`、`100元内`、`100-300元`、`300元以上`；默认 `100元内` |
| `chinese_required` | 布尔值 | 否 | 是否必须支持中文；默认 `false` |
| `notes` | 字符串或 `null` | 否 | 补充说明，最长 1000 个字符 |

## 成功响应

```json
{
  "code": 200,
  "message": "偏好接收成功，正在生成推荐...",
  "data": {
    "platforms": ["PC", "Switch"],
    "game_types": ["动作", "RPG"]
  }
}
```

## 校验失败

字段缺失、数组为空或传入未定义的选项时，接口返回 HTTP `422`，响应体包含字段级错误信息。
