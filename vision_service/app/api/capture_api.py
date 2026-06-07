from fastapi import APIRouter
from app.shared.state import (
    vision_mode_manager
)
import time

router = APIRouter()

@router.post("/capture")
async def capture_image():

    try:

        capture_mode = (
            vision_mode_manager
            .capture_image_mode
        )

        # RESET LAST IMAGE
        capture_mode.last_saved_path = None

        # SWITCH MODE
        vision_mode_manager.set_state(
            "CAPTURE_IMAGE"
        )

        # WAIT FOR PIPELINE TO SAVE IMAGE
        timeout = 5

        start_time = time.time()

        while (
            capture_mode.last_saved_path
            is None
        ):

            elapsed = (
                time.time() - start_time
            )

            if elapsed > timeout:

                return {
                    "success": False,
                    "message": "capture timeout"
                }

            time.sleep(0.1)

        return {
            "success": True,
            "imagePath":
                capture_mode.last_saved_path
        }

    except Exception as exception:

        print(
            f"\n[CAPTURE API ERROR]\n"
            f"{exception}\n"
        )

        return {
            "success": False
        }