# 游戏数据模块

这是 AI 游戏推荐项目中的游戏数据子模块。项目使用 Python 标准库提供本地数据接口，浏览器中的目录页面负责筛选、卡片浏览、详情和分页加载展示。

## 快速运行

需要 Python 3.10 或更高版本。在项目根目录双击 `start.bat`，或执行：

```powershell
py main.py
```

服务启动后会自动打开 `http://127.0.0.1:18800`。这个独立端口不会与项目主后端的 `8000` 端口冲突。关闭运行命令窗口或按 `Ctrl+C` 可以停止服务。

## 项目结构

```text
GameData-Model/
|-- frontend/
|   `-- index.html                 # 卡片式游戏目录页面
|-- backend/
|   |-- app.py                     # 本地 HTTP 服务和 API 路由
|   |-- data/games.json            # 游戏数据
|   |-- src/
|   |   |-- models/game.py         # 游戏数据模型
|   |   |-- repositories/          # JSON 数据访问层
|   |   `-- services/              # 查询、筛选和统计逻辑
|   `-- tests/                     # 后端测试
|-- docs/api_contract.md           # 接口约定
|-- main.py                        # 启动入口
|-- start.bat                      # 双击启动脚本
`-- .gitignore
```

## 已实现功能

- 游戏列表、详情和 60 条演示游戏数据。
- 通过 `GET /api/games` 获取游戏数据，支持关键词、类型、平台、标签筛选、排序和 `page`/`size` 分页。
- 主目录为卡片式无限加载：滚动到末尾会继续取下一页，同时保留可访问的“加载更多游戏”按钮。
- 选择卡片后，在同页详情面板显示平台、开发商、简介和玩家评价占比，不需要跳转或依赖图表初始化。
- 已知 Steam App ID 的游戏会在本地生成封面显示后异步替换为 Steam CDN 封面；无网络、Steam 不可访问或非 Steam 游戏始终使用本地 SVG 封面。
- 前端不再依赖 ECharts 或其他在线脚本，目录内容可以先于所有外部资源正常显示。
- 前端与后端在目录和运行职责上分离，后续可替换为 FastAPI、SQLite 或团队统一后端。

## GitHub 上传建议

`.gitignore` 已忽略 Python 缓存、虚拟环境和常见 IDE 配置。提交前建议执行：

```powershell
git status
git add .
git commit -m "feat: add game data dashboard"
```

如果仓库此前已经提交过 `.idea/`，Git 不会因为新增 `.gitignore` 自动停止跟踪它。保留本地配置但不再上传时，可额外执行：

```powershell
git rm -r --cached .idea
```

## 验证

在 `GameData-Model` 目录执行：

```powershell
python -m unittest backend.tests.test_game_service backend.tests.test_catalogue_api
```

页面会从本地后端请求最新游戏数据；修改 `backend/data/games.json` 后，刷新网页即可看到新的目录和本地回退封面。
