from app.utils.finger_utils \
    import FingerUtils

class OpenPalmGesture:

    def score(self, landmarks):

        states = \
            FingerUtils.get_finger_states(
                landmarks
            )

        score = 0

        if states["index"]:
            score += 1

        if states["middle"]:
            score += 1

        if states["ring"]:
            score += 1

        if states["pinky"]:
            score += 1

        # REQUIRE thumb away from palm

        thumb_tip = landmarks[4]

        index_mcp = landmarks[5]

        thumb_distance = abs(
            thumb_tip.x - index_mcp.x
        ) + abs(
            thumb_tip.y - index_mcp.y
        )

        if thumb_distance > 0.25:
            score += 1

        return score / 5

    def name(self):

        return "Open Palm"