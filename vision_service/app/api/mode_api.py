from fastapi import APIRouter

from app.controllers.vision_controller import (
    VisionController
)

from app.models.requests import (
    ModeRequest
)

router = APIRouter()

controller = VisionController()


@router.post("/mode")
async def change_mode(
    data: ModeRequest
):

    return controller.set_mode(
        data.mode
    )