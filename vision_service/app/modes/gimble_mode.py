# app/modes/gimble_mode.py
import cv2

from app.detectors.face_detectors import FaceDetector
from app.trackers.gimble_tracker import GimbalTracker
from app.trackers.target_tracker import TargetTracker
from app.controllers.esp32_controller import ESP32Controller
from app.processors.annotation_drawer import AnnotationDrawer
from app.controllers.esp32_udp_controller import ESP32ControllerUDP
from app.controllers.tuning_server import TuningServer


class GimbalMode:

    def __init__(self):
        self.detector = FaceDetector()
        self.target_tracker = TargetTracker()
        self.gimbal = GimbalTracker()
        self.esp32 = ESP32ControllerUDP()
        self.drawer = AnnotationDrawer()
        # --- live tuning bench bridge (daemon thread; doesn't touch the loop) ---
        self.tuning = TuningServer(
            tracker=self.gimbal,            # GimbalTracker -> telemetry + live params
            transport=self.esp32,           # gives sent_pan / sent_tilt on the scope
            target_tracker=self.target_tracker,  # multi-face params
            host="0.0.0.0", port=8765,
        ).start()

    def process(self, frame):

        
        # print("[GIMBAL MODE] processing frame")
        detections = self.detector.detect(frame)

        tracks, locked_id = self.target_tracker.update(detections)

        target_bbox = None
        if locked_id is not None:
            target_bbox = tracks[locked_id].bbox

        command = self.gimbal.track(
            target_bbox,
            frame.shape[1],
            frame.shape[0]
        )

        # print(f"Gimbal command: {command}")

        if command:
            self.esp32.move(command["pan"], command["tilt"])

        # frame = self.drawer.draw(frame, detections)
        self._draw_lock(frame, tracks, locked_id)
        h, w = frame.shape[:2]

        cv2.line(frame, (w//2, 0), (w//2, h), (0,255,255), 2)
        cv2.line(frame, (0, h//2), (w, h//2), (0,255,255), 2)

        # ==========================================
        # DEBUG OVERLAY
        # ==========================================

        h, w = frame.shape[:2]

        # frame center
        center_x = w // 2
        center_y = h // 2

        # yellow reference cross
        cv2.line(frame, (center_x, 0), (center_x, h), (0, 255, 255), 2)
        cv2.line(frame, (0, center_y), (w, center_y), (0, 255, 255), 2)

        # cv2.putText(
        #     frame,
        #     f"FRAME CENTER: ({center_x},{center_y})",
        #     (10, 25),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     0.6,
        #     (0, 255, 255),
        #     2
        # )

        # locked target information
        # if target_bbox is not None:
        #     x1, y1, x2, y2 = target_bbox

        #     face_x = int((x1 + x2) / 2)
        #     face_y = int((y1 + y2) / 2)

        #     # face center marker
        #     cv2.circle(frame, (face_x, face_y), 8, (0, 0, 255), -1)

        #     # line from frame center to face center
        #     cv2.line(
        #         frame,
        #         (center_x, center_y),
        #         (face_x, face_y),
        #         (255, 0, 255),
        #         2
        #     )

        #     # bbox coordinates
        #     cv2.putText(
        #         frame,
        #         f"BBOX: ({x1},{y1}) ({x2},{y2})",
        #         (10, 55),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.6,
        #         (0, 255, 0),
        #         2
        #     )

        #     # face center
        #     cv2.putText(
        #         frame,
        #         f"FACE CENTER: ({face_x},{face_y})",
        #         (10, 85),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.6,
        #         (0, 255, 0),
        #         2
        #     )

        #     # error values
        #     cv2.putText(
        #         frame,
        #         f"ERROR: ({face_x-center_x},{face_y-center_y})",
        #         (10, 115),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.6,
        #         (0, 0, 255),
        #         2
        #     )

        #     # current servo values
        #     cv2.putText(
        #         frame,
        #         f"PAN={self.gimbal.pan:.1f} TILT={self.gimbal.tilt:.1f}",
        #         (10, 145),
        #         cv2.FONT_HERSHEY_SIMPLEX,
        #         0.6,
        #         (255, 255, 255),
        #         2
        #     )
        return frame

    def _draw_lock(self, frame, tracks, locked_id):
        if locked_id is None or locked_id not in tracks:
            return
        x1, y1, x2, y2 = tracks[locked_id].bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(frame, "LOCK", (x1, y2 + 18),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)