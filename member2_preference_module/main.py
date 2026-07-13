"""AI 游戏推荐应用 - 用户偏好输入模块。直接运行本文件即可启动。"""

from typing import Literal
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


Platform = Literal["PC", "Switch", "PS5", "Xbox", "手机"]
GameType = Literal["动作", "RPG", "射击", "策略", "模拟经营", "休闲", "独立游戏"]


class UserPreference(BaseModel):
    """前端提交的游戏偏好数据。"""

    platforms: list[Platform] = Field(
        ..., min_length=1, description="至少选择一个游戏平台"
    )
    game_types: list[GameType] = Field(
        ..., min_length=1, description="至少选择一个游戏类型"
    )
    player_mode: Literal["单人", "本地多人", "在线多人", "MMO"] = "单人"
    art_styles: list[str] = Field(default_factory=list)
    duration_preference: Literal["短平快(<10h)", "适中(10-30h)", "杀时间(30h+)", "无限游玩"] = (
        "适中(10-30h)"
    )
    budget: Literal["免费", "100元内", "100-300元", "300元以上"] = "100元内"
    chinese_required: bool = False
    notes: str | None = Field(default=None, max_length=1000)


app = FastAPI(
    title="AI Game Recommendation API",
    description="用户偏好输入模块 API",
    version="1.0.0",
)

BASE_DIR = Path(__file__).resolve().parent

# 允许 file:// 直接打开的前端页面向本地接口发起请求。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """用于确认本地服务是否运行。"""
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    """提供同目录中的前端页面。"""
    return FileResponse(BASE_DIR / "index.html")


@app.post("/api/preferences/submit")
def submit_preferences(preference: UserPreference) -> dict[str, object]:
    """接收并回显用户偏好，后续可在此接入推荐引擎。"""
    received_data = preference.model_dump()
    print(f"收到用户游戏偏好: {received_data}")

    return {
        "code": 200,
        "message": "偏好接收成功，正在生成推荐...",
        "data": received_data,
    }
