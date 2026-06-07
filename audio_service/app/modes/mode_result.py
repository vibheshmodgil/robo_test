# for resolving circular dependency
class ModeResult:

    def __init__(
        self,
        wakeword_detected=False,
        transcription_complete=False,
        text=None
    ):

        self.wakeword_detected = (
            wakeword_detected
        )

        self.transcription_complete = (
            transcription_complete
        )

        self.text = text