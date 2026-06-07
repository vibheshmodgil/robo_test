from app.detectors.yolo_detector import YoloDetector
from app.detectors.face_detectors import FaceDetector
from app.trackers.centroid_tracker import CentroidTracker
from app.processors.annotation_drawer import AnnotationDrawer

class FollowMode:

    def __init__(self):

        self.detector = FaceDetector()
        self.tracker = CentroidTracker()
        self.drawer = AnnotationDrawer()

    def process(self, frame):

        detections = self.detector.detect(frame)
        tracked = self.tracker.track(detections)
        final_frame = self.drawer.draw(frame,tracked)
        
        return final_frame