# GAME//PULSE 用户偏好模块

## 目录

- `frontend/`：用户偏好与 Steam 导入页面。
- `backend/`：FastAPI 偏好提交和 Steam 资料解析接口。
- `docs/`：接口、请求参数和 Steam 解析说明。
- `.env.example`：可选的 Steam Web API 配置示例。

## 启动

安装依赖：

```powershell
py -3 -m pip install -r requirements.txt
```

演示时直接运行：

```powershell
py -3 run_browser.py
```

服务会自动打开默认浏览器并访问 `http://127.0.0.1:8000`。

开发调试时也可以使用：

```powershell
py -3 -m uvicorn backend.main:app --reload
```

这是项目唯一的前端打开方式，便于演示和讲解：浏览器页面提交表单，FastAPI 直接返回接口结果。

接口说明见 `docs/PREFERENCE_API.md`，交互式接口文档位于 `http://127.0.0.1:8000/docs`。
