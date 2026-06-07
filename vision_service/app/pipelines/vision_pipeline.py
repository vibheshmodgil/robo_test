import cv2

from app.cameras.webcam_camera import WebcamCamera
from app.shared.state import (
    vision_mode_manager
)



class VisionPipeline:

    def __init__(self):
        # Change Camera
        self.camera = WebcamCamera(
            "http://192.168.1.9:81/stream"
        )
        # self.camera = WebcamCamera()
        self.vision_mode_manager = (
            vision_mode_manager
        )

    def start(self):
        try:
            while True:

                frame = self.camera.get_frame()

                if frame is None:
                    continue

                frame = cv2.resize(
                    frame,
                    (640, 480)
                )

                current_handler = (
                    self.vision_mode_manager
                    .get_current_handler()
                )

                processed_frame = (
                    current_handler
                    .process(frame)
                )

                cv2.imshow(
                    "Vision Service",
                    processed_frame
                )

                if cv2.waitKey(1) & 0xFF == 27:
                    break
                
        except KeyboardInterrupt:
            print("\n[VisionPipeline] Stopping pipeline...")

        finally:
            print("[VisionPipeline] Cleaning up")
            cv2.destroyAllWindows()
        