from ultralytics import YOLO


class PersonDetector:

    def __init__(self):

        self.model = YOLO(
            "yolov8n.pt"
        )

    def detect(
        self,
        frame
    ):

        results = (
            self.model(
                frame,
                verbose=False
            )
        )

        detections = []

        for result in results:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                label = (
                    self.model.names[
                        class_id
                    ]
                )

                if (
                    label == "person"
                    and confidence > 0.5
                ):

                    x1, y1, x2, y2 = (
                        map(
                            int,
                            box.xyxy[0]
                        )
                    )

                    detections.append({

                        "label":
                            label,

                        "confidence":
                            confidence,

                        "bbox":
                            (
                                x1,
                                y1,
                                x2,
                                y2
                            )
                    })

        return detections