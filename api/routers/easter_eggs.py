from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

_DOCKER_DIR = Path(__file__).resolve().parent.parent.parent / "docker"


@router.get("/bonus/dora")
async def bonus_dora() -> FileResponse:
    return FileResponse(_DOCKER_DIR / "bonus.jpg", media_type="image/jpeg")


@router.get("/fine/mem")
async def fine_mem() -> FileResponse:
    return FileResponse(_DOCKER_DIR / "fine.jpg", media_type="image/jpeg")
