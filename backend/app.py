from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import get_settings
from backend.models import (
    GameDetailResponse,
    KeyCheckRequest,
    KeyCheckResponse,
    RecommendRequest,
    RecommendResponse,
)
from backend.services.ai_service import AiServiceError
from backend.services.game_service import GameDataError, GameNotFoundError, get_game_detail
from backend.services.key_service import build_key_check_result
from backend.services.recommend_service import generate_recommendations


app = FastAPI(title="成员4 AI 推荐模块", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
def settings_page():
    return FileResponse("frontend/settings.html")


@app.get("/api/health")
def health():
    return {"success": True, "message": "member4 ai module is running"}


@app.get("/games/{game_id}", include_in_schema=False)
def game_detail_page(game_id: str):
    return FileResponse("frontend/game-detail.html")


@app.get("/api/games/{game_id}", response_model=GameDetailResponse)
def game_detail(game_id: str):
    try:
        return GameDetailResponse(data=get_game_detail(game_id))
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail="游戏不存在") from exc
    except GameDataError as exc:
        raise HTTPException(status_code=500, detail="游戏数据暂时不可用") from exc


@app.post("/api/key/check", response_model=KeyCheckResponse)
def check_key(payload: KeyCheckRequest):
    settings = get_settings()
    return KeyCheckResponse(data=build_key_check_result(payload.api_key, settings))


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(
    payload: RecommendRequest,
    x_ai_api_key: str | None = Header(default=None, alias="x-ai-api-key"),
):
    settings = get_settings()
    try:
        return generate_recommendations(payload, x_ai_api_key, settings)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AiServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

