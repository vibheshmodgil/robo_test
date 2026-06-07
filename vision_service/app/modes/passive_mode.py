from app.detectors.motion_detector import MotionDetector
from app.processors.frame_sampler import FrameSampler
from app.detectors.yolo_detector import YoloDetector
from app.analysers.movement_analyzer import MovementAnalyzer
class PassiveMode:

    def __init__(self):

        self.motion_detector = MotionDetector()
        self.sampler = FrameSampler(fps=5)
        self.processor = YoloDetector()
        self.movement_analyzer = MovementAnalyzer()

    def process(self, frame):

        if not self.sampler.should_process():
            return frame
        motion = self.motion_detector.detect(frame)
        if not motion:
            print("[PassiveMode] No movement")
        else:
            detections = self.processor.detect(frame)
            moved = self.movement_analyzer.analyze(detections)
            for label in moved:
                print(f"{label} moved")

        return frame