# 测试计划

## 当前自动检查

```powershell
python -m unittest discover -s backend/tests -v
python -m unittest discover -s tests -v
cd frontend
npm run build
```

统一 API 测试覆盖健康检查、游戏列表与详情 ID 一致性、本地推荐、收藏 CRUD 和历史自动保存。成员四兼容测试继续保留。

## 待补充

- Steam 公共、私密、无效和网络失败场景的 mock 测试。
- AI 上游超时、401、非 JSON 响应测试。
- 收藏和历史的多用户隔离、并发写入和数据库迁移测试。
- Playwright 端到端流程：偏好提交、推荐生成、详情跳转。
- 桌面和移动视口的视觉回归检查。
