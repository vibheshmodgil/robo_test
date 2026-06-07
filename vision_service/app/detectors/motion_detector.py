import cv2
from app.interfaces.detector_interface import DetectorInterface

class MotionDetector(DetectorInterface):

    def __init__(self):

        self.previous_frame = None

    def detect(self, frame):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        gray = cv2.GaussianBlur(
            gray,
            (21,21),
            0
        )

        if self.previous_frame is None:

            self.previous_frame = gray

            return False

        diff = cv2.absdiff(
            self.previous_frame,
            gray
        )

        thresh = cv2.threshold(
            diff,
            25,
            255,
            cv2.THRESH_BINARY
        )[1]

        motion = thresh.sum() > 50000

        self.previous_frame = gray
        
        return motion