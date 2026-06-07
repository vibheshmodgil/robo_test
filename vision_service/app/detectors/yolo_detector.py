from ultralytics import YOLO
from app.interfaces.detector_interface import DetectorInterface

class YoloDetector(DetectorInterface):

    def __init__(self):

        self.model = YOLO("yolov8n.pt")

    def detect(self, frame):

        results = self.model(frame,verbose=False)
        detections = []

        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )
                cls = int(box.cls[0])
                confidence = float(box.conf[0])
                label = self.model.names[cls]
                detections.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2]
                })

        return detections