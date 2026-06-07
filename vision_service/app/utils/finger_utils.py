class FingerUtils:

    @staticmethod
    def get_finger_states(
        landmarks
    ):

        states = {}

        states["index"] = (

            landmarks[8].y <
            landmarks[6].y and

            landmarks[6].y <
            landmarks[5].y
        )

        states["middle"] = (

            landmarks[12].y <
            landmarks[10].y and

            landmarks[10].y <
            landmarks[9].y
        )

        states["ring"] = (

            landmarks[16].y <
            landmarks[14].y and

            landmarks[14].y <
            landmarks[13].y
        )

        states["pinky"] = (

            landmarks[20].y <
            landmarks[18].y and

            landmarks[18].y <
            landmarks[17].y
        )

        return states