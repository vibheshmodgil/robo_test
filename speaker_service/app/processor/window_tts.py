import pyttsx3


class WindowTTS:

    def speak(
        self,
        text
    ):

        print(
            f"\n[SPEAKER] {text}\n"
        )

        engine = pyttsx3.init()

        engine.setProperty(
            "rate",
            180
        )

        engine.say(
            text
        )

        engine.runAndWait()