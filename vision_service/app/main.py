import threading

import uvicorn

from fastapi import FastAPI

from app.api.mode_api import (
    router as mode_router
)

from app.api.hud_api import (
    router as hud_router
)

from app.api.capture_api import (
    router as capture_router
)

from app.pipelines.vision_pipeline import (
    VisionPipeline
    
)
from app.models.hologram_panel import (
    HologramPanel
)

from app.shared.hud_manager import (
    hud_manager
)

app = FastAPI()

app.include_router(
    mode_router
)

app.include_router(
    hud_router
)

app.include_router(
    capture_router
)

pipeline = (
    VisionPipeline()
)


def start_api():

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003
    )


if __name__ == "__main__":

    api_thread = threading.Thread(
        target=start_api,
        daemon=True
    )

    api_thread.start()

    pipeline.start()