from pydantic import BaseModel


class ModeRequest(
    BaseModel
):
    mode: str


class HudPanelRequest(
    BaseModel
):
    title: str

    message: str

    options: list[str] = []