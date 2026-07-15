from fastapi import APIRouter

from backend.src.services.steam_service import (
    SteamPreferenceSummary,
    SteamProfileRequest,
    read_public_steam_profile,
)

router = APIRouter(prefix="/api/steam", tags=["steam"])


@router.post("/profile", response_model=SteamPreferenceSummary)
def parse_steam_profile(payload: SteamProfileRequest) -> SteamPreferenceSummary:
    return read_public_steam_profile(payload.steam_identifier)
