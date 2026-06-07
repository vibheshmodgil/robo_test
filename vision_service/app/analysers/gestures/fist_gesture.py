from app.utils.finger_utils \
    import FingerUtils

class FistGesture:

    def score(self, landmarks):

        states = \
            FingerUtils.get_finger_states(
                landmarks
            )

        score = 0

        # fingers folded

        if not states["index"]:
            score += 1

        if not states["middle"]:
            score += 1

        if not states["ring"]:
            score += 1

        if not states["pinky"]:
            score += 1

        # thumb tucked

        thumb_tip = landmarks[4]

        wrist = landmarks[0]

        thumb_distance = abs(
            thumb_tip.x - wrist.x
        ) + abs(
            thumb_tip.y - wrist.y
        )

        if thumb_distance < 0.25:
            score += 1

        return score / 5

    def name(self):

        return "Fist"