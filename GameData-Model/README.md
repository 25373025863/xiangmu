# 游戏数据模块

这是 AI 游戏推荐项目中的游戏数据子模块。项目使用 Python 标准库提供本地数据接口，浏览器中的 ECharts 页面负责游戏列表、详情、折线图和评分环图展示。

## 快速运行

需要 Python 3.10 或更高版本。在项目根目录双击 `start.bat`，或执行：

```powershell
py main.py
```

服务启动后会自动打开 `http://127.0.0.1:8000`。关闭运行命令窗口或按 `Ctrl+C` 可以停止服务。

## 项目结构

```text
GameData-Model/
|-- frontend/
|   `-- index.html                 # ECharts 单页数据总览
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
- 通过 `GET /api/games` 获取游戏数据，支持关键词、类型、平台、标签筛选。
- ECharts 折线图展示评分指数、价格指数、平台覆盖和标签丰富度。
- 默认环图展示总体评价分布；点击游戏列表或折线图数据点后，环图切换为该游戏的好评、中等、差评百分比。
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

## 图表说明

ECharts 通过在线资源加载，因此浏览器需要联网。页面会从本地后端请求最新游戏数据；修改 `backend/data/games.json` 后，刷新网页即可看到新的图表结果。
