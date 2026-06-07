import numpy as np

from app.renderers.hologram_renderer import HologramRenderer
from app.detectors.face_detectors import FaceDetector


class InventoryVisionMode:
    """
    Vision handler for the INVENTORY state.

    Panels are owned entirely by the backend (Java) through the HUD API, which
    drives the single shared panel in hud_manager. This handler therefore does
    NOT create panels anymore (that was causing a second, competing panel).
    It only does the camera-side work: face tracking + rendering the HUD.
    """

    def __init__(self):
        self.renderer = HologramRenderer()
        self.detector = FaceDetector()
        self.smooth_face_box = None

    def process(self, frame):
        face_box = None
        detections = self.detector.detect(frame)

        if detections:
            x1, y1, x2, y2 = detections[0]["bbox"]
            new_box = np.array(
                [x1, y1, x2 - x1, y2 - y1],
                dtype=np.float32,
            )

            if self.smooth_face_box is None:
                self.smooth_face_box = new_box
            else:
                alpha = 0.85
                self.smooth_face_box = (
                    self.smooth_face_box * alpha + new_box * (1.0 - alpha)
                )

            face_box = tuple(self.smooth_face_box.astype(int))

        return self.renderer.render(frame, face_box)