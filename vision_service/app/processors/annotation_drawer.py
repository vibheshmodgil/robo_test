import cv2

class AnnotationDrawer:

    def draw(self, frame, detections):

        for detection in detections:

            x1, y1, x2, y2 = \
                detection["bbox"]

            label = detection["label"]

            object_id = detection["id"]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0,255,0),
                2
            )

            cv2.putText(
                frame,
                f"{label} #{object_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0,255,0),
                2
            )

        return frame