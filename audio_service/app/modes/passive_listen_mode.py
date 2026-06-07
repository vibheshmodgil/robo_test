from app.modes.base_mode import (
    BaseMode
)

from app.modes.mode_result import (
    ModeResult
)


class PassiveListenMode(BaseMode):

    def __init__(
        self,
        wakeword_detector
    ):

        self.wakeword_detector = (
            wakeword_detector
        )

    def on_enter(self):

        print(
            "\n[MODE] PASSIVE MODE\n"
        )

    def on_exit(self):

        pass

    def process_audio(
        self,
        audio_chunk
    ):

        detected = (
            self.wakeword_detector.detect(
                audio_chunk
            )
        )

        if detected:

            return ModeResult(
                wakeword_detected=True
            )

        return None