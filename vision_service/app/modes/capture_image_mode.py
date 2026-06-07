import cv2

from pathlib import Path

from datetime import datetime

downloads_path = (
    Path.home()
    / "Downloads"
    / "inventory_images"
)

class CaptureImageMode:

    def __init__(self):

        self.last_saved_path = None

    def process(
        self,
        frame
    ):

        try:

            Path(
                "inventory_images"
            ).mkdir(
                exist_ok=True
            )

            timestamp = (
                datetime.now()
                .strftime(
                    "%Y%m%d_%H%M%S"
                )
            )

            filename = (
                f"{downloads_path}"
                f"inventory_{timestamp}.jpg"
            )

            cv2.imwrite(
                filename,
                frame
            )

            self.last_saved_path =filename

            print(
                f"\n[IMAGE SAVED]"
                f"\n{filename}\n"
            )

            from app.shared.state import (
                vision_mode_manager
            )

            vision_mode_manager.set_state(
                "PASSIVE"
            )

            return frame

        except Exception as exception:

            print(exception)

            return frame