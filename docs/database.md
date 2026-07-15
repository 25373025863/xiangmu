# 数据结构

当前阶段使用 JSON 文件，活动数据目录为 `backend/src/data/`。

## 游戏

`games.json` 是唯一活动游戏数据源。稳定 ID 统一使用 `g001` 格式，推荐结果、详情页和后续收藏记录必须复用该 ID。

必填字段：`id`、`title`、`genres`、`platforms`、`tags`、`description`。可选字段：`price`、`score`。

## 收藏

`favorites.json` 保存收藏时的游戏快照和 `favorited_at`。`id` 复用游戏 ID，同一游戏只能收藏一次。

## 历史

`histories.json` 在每次推荐成功时追加 `id`、`preferences`、`recommendations` 和 `created_at`。

旧成员目录内的数据文件仅作为迁移来源，不属于活动运行时，禁止新代码继续引用。
