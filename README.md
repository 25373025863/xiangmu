# AI 游戏推荐应用项目分工

## 项目简介

本项目计划开发一个基于 AI API Key 的游戏推荐应用。用户可以输入自己的喜好，例如游戏类型、平台、预算、游玩人数、画风偏好、时长偏好等，系统通过 AI 分析用户需求，并推荐合适的游戏。

核心目标：

- 根据用户偏好生成个性化游戏推荐
- 支持多维度筛选，例如平台、类型、价格、评分、多人/单人
- 使用 AI API 生成推荐理由和对比分析
- 提供简洁易用的前端界面
- 支持用户在应用中输入和更换自己的 AI API Key
- 保证项目默认 API Key 不写进前端代码，也不上传到 GitHub

## 8 人团队分工

分工原则：每个人都要同时参与前端和后端开发。为了避免重复工作，8 个人分别负责不同功能模块，每个模块都要完成页面、接口、联调和简单测试。

### 1. 成员一：首页与项目整体协调

负责应用首页、项目基础结构和整体进度协调。

前端任务：

- 实现首页布局和导航入口
- 展示项目名称、应用简介和开始推荐按钮
- 统一基础页面风格，例如颜色、字体、按钮样式

后端任务：

- 搭建后端项目基础结构
- 实现健康检查接口，例如 `/api/health`
- 统一后端接口返回格式

交付物：

- 首页页面
- 后端基础服务
- 项目运行说明

### 2. 成员二：用户偏好输入模块

负责用户填写游戏偏好的完整流程。

前端任务：

- 实现偏好输入页面
- 实现游戏类型、平台、预算、人数等表单控件
- 完成表单校验和提交按钮状态

后端任务：

- 设计并实现用户偏好提交接口
- 校验前端提交的数据是否合法
- 将用户偏好整理成后续推荐模块可使用的数据格式

交付物：

- 偏好输入页面
- 用户偏好提交接口
- 请求参数说明

### 3. 成员三：游戏数据模块

负责游戏基础数据的展示、存储和查询。

前端任务：

- 实现游戏库浏览页面
- 实现游戏标签、平台、价格等基础信息展示
- 实现简单筛选和搜索界面

后端任务：

- 整理游戏数据文件或数据库表
- 实现游戏列表查询接口
- 实现按类型、平台、标签筛选游戏的接口逻辑

交付物：

- 游戏库页面
- 游戏数据文件或数据库表
- 游戏查询接口

### 4. 成员四：AI 推荐模块

负责 AI 推荐逻辑和推荐结果生成。

前端任务：

- 实现 API Key 设置入口，支持用户输入、更换和清除自己的 API Key
- 在页面中隐藏显示 API Key，只展示部分脱敏内容
- 实现推荐生成中的加载状态
- 展示 AI 推荐结果的基础结构
- 处理推荐失败时的错误提示

后端任务：

- 调用 AI API 生成游戏推荐
- 设计推荐 prompt
- 解析 AI 返回结果并转换成前端需要的 JSON 格式
- 支持从请求头读取用户自己的 API Key
- 如果用户没有提供 API Key，则使用后端 `.env` 中配置的默认 API Key
- 后端不能打印、返回或保存用户的真实 API Key

交付物：

- AI 推荐接口
- API Key 设置页面或设置弹窗
- prompt 模板
- 推荐结果数据格式说明

### 5. 成员五：推荐结果展示模块

负责推荐列表和推荐卡片。

前端任务：

- 实现推荐结果页面
- 实现游戏推荐卡片，包括名称、平台、类型、推荐理由
- 实现空结果、加载中、请求失败等状态

后端任务：

- 优化推荐结果接口返回字段
- 增加推荐结果排序逻辑
- 为每个推荐结果补充推荐理由、匹配标签和缺点说明

交付物：

- 推荐结果页
- 游戏推荐卡片组件
- 推荐结果接口

### 6. 成员六：游戏详情模块

负责单个游戏的详情展示。

前端任务：

- 实现游戏详情页
- 展示游戏名称、封面、标签、平台、简介和推荐理由
- 实现从推荐列表跳转到详情页

后端任务：

- 实现游戏详情查询接口
- 根据游戏 ID 返回完整游戏信息
- 处理游戏不存在时的错误返回

交付物：

- 游戏详情页
- 游戏详情接口
- 页面跳转逻辑

### 7. 成员七：收藏与历史记录模块

负责用户收藏推荐结果和查看历史记录。

前端任务：

- 实现收藏按钮和收藏列表页面
- 实现历史推荐记录页面
- 展示用户曾经输入过的偏好和对应推荐结果

后端任务：

- 实现收藏接口
- 实现历史记录保存和查询接口
- 设计收藏和历史记录的数据结构

交付物：

- 收藏页面
- 历史记录页面
- 收藏与历史记录接口

### 8. 成员八：测试、文档与部署模块

负责项目测试、文档整理和部署，同时也要完成配套的前后端功能。

前端任务：

- 实现关于页面或帮助页面
- 展示项目成员分工、使用说明和注意事项
- 检查页面在不同屏幕尺寸下的显示效果

后端任务：

- 实现项目配置检查接口
- 检查 AI API Key 是否已配置，但不能返回真实密钥
- 整理接口测试用例并协助部署后端服务

交付物：

- 帮助页面
- 配置检查接口
- 测试用例和部署说明

## 推荐功能模块

### 用户偏好输入

用户可以输入或选择：

- 喜欢的游戏类型
- 使用的平台，例如 PC、Switch、PlayStation、Xbox、手机
- 预算范围
- 单人或多人
- 喜欢的画风
- 希望游戏时长
- 是否需要中文支持

### API Key 设置

用户可以在应用中自行配置 AI API Key：

- 输入自己的 AI API Key
- 随时更换新的 API Key
- 一键清除已经保存的 API Key
- 推荐请求时优先使用用户自己的 API Key
- 如果用户没有填写，则使用后端配置的默认 API Key

建议保存方式：

- 演示版本：保存在浏览器 `sessionStorage`，关闭浏览器后自动失效
- 本地开发版本：可以选择保存在 `localStorage`
- 正式上线版本：不建议长期保存用户 API Key，除非后端做加密存储和账号权限控制

### AI 推荐结果

每个推荐结果建议包含：

- 游戏名称
- 推荐理由
- 适合的玩家类型
- 游戏平台
- 游戏标签
- 可能的缺点
- 相似游戏推荐

### 游戏详情页

详情页建议包含：

- 游戏基础信息
- 游戏截图或封面
- 类型和标签
- 推荐理由
- 适合人群
- 购买或了解更多链接

## 基础技术方案

可以采用以下技术组合：

- 前端：HTML/CSS/JavaScript 或 React
- 后端：Node.js/Express 或 Python/FastAPI
- AI 接口：通过后端调用 AI API
- 数据存储：JSON 文件、SQLite 或其他轻量数据库
- 部署：GitHub Pages、Vercel、Render 或其他平台

## 项目结构架构设计

推荐采用前后端分离架构。前端只负责页面展示和用户交互，后端负责接口、游戏数据处理、AI API 调用和 API Key 保护。

整体流程：

1. 用户在前端设置或更换自己的 AI API Key
2. 用户在前端填写游戏偏好
3. 前端把用户偏好和脱敏后的 Key 状态提交给后端，真实 Key 通过请求头传递
4. 后端读取游戏数据并组合 AI prompt
5. 后端优先使用用户请求头中的 API Key 调用 AI API
6. 如果用户没有提供 API Key，后端使用 `.env` 中的默认 API Key
7. 后端把推荐结果返回给前端展示

推荐文件夹目录：

```text
xiangmu/
├── README.md
├── .gitignore
├── .env.example
├── docs/
│   ├── api.md
│   ├── database.md
│   └── test-plan.md
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── public/
│   │   └── images/
│   └── src/
│       ├── main.js
│       ├── App.js
│       ├── api/
│       │   ├── request.js
│       │   ├── gameApi.js
│       │   ├── keyApi.js
│       │   └── recommendApi.js
│       ├── assets/
│       ├── components/
│       │   ├── GameCard.js
│       │   ├── Loading.js
│       │   └── Navbar.js
│       ├── pages/
│       │   ├── HomePage.js
│       │   ├── PreferencePage.js
│       │   ├── RecommendPage.js
│       │   ├── GameDetailPage.js
│       │   ├── FavoritePage.js
│       │   ├── SettingsPage.js
│       │   └── HelpPage.js
│       ├── router/
│       │   └── index.js
│       ├── styles/
│       │   ├── global.css
│       │   └── variables.css
│       └── utils/
│           └── format.js
├── backend/
│   ├── package.json
│   ├── src/
│   │   ├── app.js
│   │   ├── server.js
│   │   ├── config/
│   │   │   └── env.js
│   │   ├── routes/
│   │   │   ├── healthRoutes.js
│   │   │   ├── gameRoutes.js
│   │   │   ├── recommendRoutes.js
│   │   │   ├── keyRoutes.js
│   │   │   ├── favoriteRoutes.js
│   │   │   └── historyRoutes.js
│   │   ├── controllers/
│   │   │   ├── gameController.js
│   │   │   ├── recommendController.js
│   │   │   ├── keyController.js
│   │   │   ├── favoriteController.js
│   │   │   └── historyController.js
│   │   ├── services/
│   │   │   ├── aiService.js
│   │   │   ├── gameService.js
│   │   │   ├── keyService.js
│   │   │   ├── recommendService.js
│   │   │   └── promptService.js
│   │   ├── data/
│   │   │   ├── games.json
│   │   │   ├── favorites.json
│   │   │   └── histories.json
│   │   ├── middlewares/
│   │   │   ├── errorHandler.js
│   │   │   └── validateRequest.js
│   │   └── utils/
│   │       └── response.js
│   └── tests/
│       ├── game.test.js
│       ├── key.test.js
│       └── recommend.test.js
└── scripts/
    └── seed-data.js
```

## 目录说明

- `frontend/`：前端项目目录，负责页面、组件、样式和接口请求。
- `frontend/src/pages/`：页面级文件，例如首页、偏好输入页、推荐结果页、详情页。
- `frontend/src/components/`：可复用组件，例如游戏卡片、导航栏、加载提示。
- `frontend/src/api/`：统一管理前端请求后端接口的代码。
- `frontend/src/pages/SettingsPage.js`：用户设置或更换自己的 AI API Key。
- `backend/`：后端项目目录，负责接口、业务逻辑、数据处理和 AI API 调用。
- `backend/src/routes/`：接口路由，只负责定义接口路径。
- `backend/src/controllers/`：接收请求、调用服务、返回响应。
- `backend/src/services/`：核心业务逻辑，例如 AI 推荐、游戏查询、prompt 生成。
- `backend/src/services/keyService.js`：检查用户传入的 API Key 是否存在、格式是否合理，但不能保存真实 Key。
- `backend/src/data/`：临时存放游戏数据、收藏数据和历史记录数据。
- `backend/src/config/`：读取环境变量，例如 AI API Key。
- `docs/`：项目文档，例如接口文档、数据结构说明、测试计划。

## 建议接口设计

| 功能 | 请求方法 | 接口路径 | 说明 |
| --- | --- | --- | --- |
| 健康检查 | GET | `/api/health` | 检查后端是否启动 |
| 游戏列表 | GET | `/api/games` | 获取游戏数据 |
| 游戏详情 | GET | `/api/games/:id` | 获取单个游戏详情 |
| Key 检查 | POST | `/api/key/check` | 检查用户 API Key 是否可用，不返回真实 Key |
| AI 推荐 | POST | `/api/recommend` | 根据用户偏好生成推荐，支持请求头 `x-ai-api-key` |
| 收藏游戏 | POST | `/api/favorites` | 收藏某个游戏 |
| 收藏列表 | GET | `/api/favorites` | 获取收藏记录 |
| 历史记录 | GET | `/api/histories` | 获取推荐历史 |
| 配置检查 | GET | `/api/config/check` | 检查后端配置是否完整 |

## 分工与目录对应

| 成员 | 负责模块 | 主要前端目录 | 主要后端目录 |
| --- | --- | --- | --- |
| 成员一 | 首页与项目整体协调 | `frontend/src/pages/HomePage.js` | `backend/src/app.js`、`backend/src/routes/healthRoutes.js` |
| 成员二 | 用户偏好输入 | `frontend/src/pages/PreferencePage.js` | `backend/src/controllers/recommendController.js` |
| 成员三 | 游戏数据 | `frontend/src/pages/GameDetailPage.js` | `backend/src/data/games.json`、`backend/src/services/gameService.js` |
| 成员四 | AI 推荐与 API Key 设置 | `frontend/src/pages/SettingsPage.js`、`frontend/src/api/keyApi.js`、`frontend/src/api/recommendApi.js` | `backend/src/services/aiService.js`、`backend/src/services/keyService.js`、`backend/src/services/promptService.js` |
| 成员五 | 推荐结果展示 | `frontend/src/pages/RecommendPage.js` | `backend/src/services/recommendService.js` |
| 成员六 | 游戏详情 | `frontend/src/components/GameCard.js` | `backend/src/routes/gameRoutes.js` |
| 成员七 | 收藏与历史记录 | `frontend/src/pages/FavoritePage.js` | `backend/src/routes/favoriteRoutes.js`、`backend/src/routes/historyRoutes.js` |
| 成员八 | 测试、文档与部署 | `frontend/src/pages/HelpPage.js` | `backend/tests/`、`docs/` |

## API Key 使用规范

本项目支持两种 API Key 使用方式：

- 默认 Key：项目方提供的默认 AI API Key，只能放在后端 `.env` 文件中。
- 用户 Key：用户在设置页输入自己的 AI API Key，可以随时更换或清除。

推荐做法：

1. 前端提供设置页，让用户输入自己的 API Key
2. 前端只保存用户自己的 API Key，不保存项目默认 API Key
3. 推荐请求时，前端通过请求头 `x-ai-api-key` 把用户 Key 传给后端
4. 后端优先使用用户传来的 Key
5. 如果用户没有填写 Key，后端才使用 `.env` 中的默认 Key
6. 后端不能把 API Key 写入日志、数据库或接口返回值
7. `.gitignore` 中必须忽略 `.env`
8. GitHub 上只提交 `.env.example`

前端保存建议：

- 优先使用 `sessionStorage`，关闭浏览器后自动清除
- 如果为了方便演示，可以使用 `localStorage`
- 页面上只显示脱敏后的 Key，例如 `sk-****abcd`

请求头示例：

```text
x-ai-api-key: user_api_key_here
```

`.env.example` 示例：

```env
DEFAULT_AI_API_KEY=your_default_api_key_here
ALLOW_USER_API_KEY=true
```

## 项目协作流程

1. 项目负责人确定本周目标
2. 每个人领取自己的任务
3. 开发前先同步接口格式和页面需求
4. 每次完成一个功能后提交代码
5. 合并前由至少一名同学检查
6. 测试负责人统一记录问题
7. 最后进行项目演示和答辩准备

## 第一阶段任务建议

第一周建议完成：

- 确定项目需求和页面流程
- 完成 UI 原型
- 搭建前端和后端基础项目
- 准备一份基础游戏数据
- 跑通一次 AI 推荐接口

第二周建议完成：

- 完成推荐结果页面
- 完成游戏详情展示
- 优化 prompt 和推荐质量
- 增加异常处理
- 完成测试和项目文档

## 最终展示重点

展示时可以重点说明：

- 用户如何输入游戏偏好
- AI 如何根据偏好生成推荐
- 推荐结果为什么适合用户
- 项目如何保护 API Key
- 团队成员分别完成了哪些工作
