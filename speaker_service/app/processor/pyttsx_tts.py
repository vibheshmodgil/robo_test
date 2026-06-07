import subprocess

from app.tts.base_tts import (
    BaseTTS
)


class PyttsxTTS(BaseTTS):

    def speak(
        self,
        text
    ):

        print(
            f"\n[SPEAKER] {text}\n"
        )

        subprocess.run(
            [
                "say",
                text
            ]
        )