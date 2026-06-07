from fastapi import APIRouter

from app.controllers.vision_controller import (
    VisionController
)

from app.models.requests import (
    HudPanelRequest
)

router = APIRouter()

controller = VisionController()


@router.post("/hud/panel")
async def create_panel(
    data: HudPanelRequest
):

    return controller.create_panel(
        data.title,
        data.message,
        data.options
    )


@router.put(
    "/hud/panel/{panel_id}"
)
async def update_panel(
    panel_id: str,
    data: HudPanelRequest
):

    return controller.update_panel(
        panel_id,
        data.title,
        data.message,
        data.options
    )


@router.post(
    "/hud/panel/{panel_id}/select"
)
async def select_panel(
    panel_id: str,
    selected: int
):

    return controller.select_panel(
        panel_id,
        selected
    )


@router.post(
    "/hud/panel/{panel_id}/close"
)
async def close_panel(
    panel_id: str
):

    return controller.close_panel(
        panel_id
    )