"""启动 GAME//PULSE 服务并在默认浏览器中打开前端页面。"""

from __future__ import annotations

import threading
import webbrowser

import uvicorn


def open_browser() -> None:
    webbrowser.open_new("http://127.0.0.1:8000")


if __name__ == "__main__":
    threading.Timer(0.8, open_browser).start()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, log_level="info")
