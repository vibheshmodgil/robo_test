from ultralytics import YOLO


class FaceDetector:

    def __init__(self):

        print("Loading YOLO Face Model...")

        self.model = YOLO(
            "app/models/yolov8n-face.pt"
        )

        print("YOLO Face Model Loaded")

    def detect(self, frame):

        detections = []

        results = self.model(
            frame,
            imgsz=320,
            conf=0.4,
            verbose=False
        )

        for result in results:

            for box in result.boxes:

                x1, y1, x2, y2 = map(
                    int,
                    box.xyxy[0]
                )

                confidence = float(
                    box.conf[0]
                )

                detections.append({
                    "label": "face",
                    "confidence": confidence,
                    "bbox": (
                        x1,
                        y1,
                        x2,
                        y2
                    )
                })

        return detections