from app.detectors.hand_detector import HandDetector
from app.analysers.gesture_analyzer import GestureAnalyzer
import cv2

class GestureMode:

    def __init__(self):

        self.detector = HandDetector()
        self.analyzer = GestureAnalyzer()

    def process(self, frame):

        landmarks, frame = self.detector.detect(frame)

        gesture = self.analyzer.analyze(landmarks)
        cv2.putText(
            frame,
            gesture,
            (50,50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0,255,0),
            2
        )

        return frame