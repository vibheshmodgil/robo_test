from app.analysers.gestures.open_palm_gesture import OpenPalmGesture
from app.analysers.gestures.fist_gesture import FistGesture
from app.analysers.gestures.thumbs_up_gesture import ThumbsUpGesture
from app.analysers.gestures.thumbs_down_gesture import ThumbsDownGesture

class GestureAnalyzer:

    def __init__(self):

        self.gestures = [

            ThumbsUpGesture(),

            ThumbsDownGesture(),

            OpenPalmGesture(),

            FistGesture()
        ]

    def analyze(self, landmarks_list):

        if not landmarks_list:

            return "No Hands"

        hand = landmarks_list[0]

        landmarks = hand.landmark

        best_score = 0

        best_gesture = "Unknown"

        for gesture in self.gestures:

            score = gesture.score(
                landmarks
            )

            if score > best_score:

                best_score = score

                best_gesture = \
                    gesture.name()

        if best_score < 0.6:

            return "Unknown"

        return best_gesture