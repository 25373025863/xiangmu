import uvicorn

from backend.src.config.settings import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "backend.src.app:app",
        host="127.0.0.1",
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
