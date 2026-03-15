from fastapi import APIRouter, HTTPException

from app.models.schemas import RoomsConfigResponse, RoomsConfigUpdateRequest, SimpleMessageResponse
from app.repositories.config_repository import ConfigRepository

router = APIRouter()
config_repo = ConfigRepository()


@router.get("/config/rooms", response_model=RoomsConfigResponse)
def get_rooms():
    try:
        return RoomsConfigResponse(rooms=config_repo.load_rooms())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/config/rooms", response_model=SimpleMessageResponse)
def update_rooms(payload: RoomsConfigUpdateRequest):
    try:
        config_repo.save_rooms(payload.rooms)
        return SimpleMessageResponse(ok=True, message="Configuração salva com sucesso.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc