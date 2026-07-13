from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import settings
from src.routes import health_routes, config_routes
from src.middleware.error_handler import error_handler

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router, prefix="/api/health", tags=["health"])
app.include_router(config_routes.router, prefix="/api/config", tags=["config"])
app.add_exception_handler(Exception, error_handler)

@app.get("/")
async def root():
    return {"code": 0, "message": f"Welcome to {settings.APP_NAME}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)