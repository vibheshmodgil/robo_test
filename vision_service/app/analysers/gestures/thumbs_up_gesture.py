from app.utils.finger_utils \
    import FingerUtils

class ThumbsUpGesture:

    def score(self, landmarks):

        states = \
            FingerUtils.get_finger_states(
                landmarks
            )

        score = 0

        if not states["index"]:
            score += 1

        if not states["middle"]:
            score += 1

        if not states["ring"]:
            score += 1

        if not states["pinky"]:
            score += 1

        thumb_tip = landmarks[4]

        thumb_joint = landmarks[3]

        if thumb_tip.y < thumb_joint.y - 0.1:
            score += 1

        return score / 5

    def name(self):

        return "Thumbs Up"