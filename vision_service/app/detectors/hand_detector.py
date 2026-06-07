import cv2
import mediapipe as mp
from app.interfaces.detector_interface import DetectorInterface
class HandDetector(DetectorInterface):

    def __init__(self):

        self.mp_hands = mp.solutions.hands

        self.hands = self.mp_hands.Hands(
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )

        self.drawer = mp.solutions.drawing_utils

    def detect(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = self.hands.process(rgb)

        landmarks = []

        if results.multi_hand_landmarks:

            for hand_landmarks in \
                results.multi_hand_landmarks:

                self.drawer.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

                landmarks.append(
                    hand_landmarks
                )

        return landmarks, frame
        