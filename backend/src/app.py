from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.src.config.settings import get_settings
from backend.src.middlewares.error_handler import (
    ai_error_handler,
    validation_error_handler,
)
from backend.src.routes import (
    catalogue_routes,
    config_routes,
    favorite_routes,
    game_routes,
    health_routes,
    history_routes,
    key_routes,
    preference_routes,
    recommend_routes,
    steam_routes,
)
from backend.src.services.ai_service import AiServiceError
from backend.src.utils.response import success

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(AiServiceError, ai_error_handler)

for route_module in (
    health_routes,
    catalogue_routes,
    preference_routes,
    steam_routes,
    game_routes,
    key_routes,
    recommend_routes,
    favorite_routes,
    history_routes,
    config_routes,
):
    app.include_router(route_module.router)

frontend_dist = settings.frontend_dir / "dist"
assets_dir = frontend_dist / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")


@app.get("/", include_in_schema=False)
def root():
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return success(
        {
            "apiDocs": "/docs",
            "frontendDevServer": "http://127.0.0.1:5173",
        },
        "统一后端已启动",
    )


@app.get("/{path:path}", include_in_schema=False)
def spa_fallback(path: str):
    index_file = frontend_dist / "index.html"
    requested_file = frontend_dist / path
    if requested_file.is_file() and frontend_dist in requested_file.resolve().parents:
        return FileResponse(requested_file)
    if index_file.exists():
        return FileResponse(index_file)
    return root()
