"""桌面应用入口：启动本地服务，并在独立窗口中显示前端页面。"""

import threading

import uvicorn
import webview

from main import app


def start_api_server() -> None:
    """在后台线程启动 API 和前端静态页面服务。"""
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_api_server, daemon=True)
    server_thread.start()

    webview.create_window(
        "GAME//PULSE - AI 游戏推荐",
        "http://127.0.0.1:8000",
        width=1180,
        height=850,
        min_size=(900, 650),
    )
    webview.start()
