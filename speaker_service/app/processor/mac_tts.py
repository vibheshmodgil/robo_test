import subprocess


class MacTTS:

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