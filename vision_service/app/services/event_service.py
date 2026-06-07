import requests


class EventService:

    def send_event(
        self,
        event
    ):

        payload = {

            "event":
                event.event_type,

            "summary":
                event.summary,

            "metadata":
                event.metadata
        }

        print(
            "\n[EVENT SERVICE] SENDING EVENT\n"
        )

        print(payload)

        try:

            # # SEND EVENT
            # requests.post(
            #     "http://127.0.0.1:9999/event",
            #     json=payload,
            #     timeout=3
            # )

            # TRIGGER SPEAKER
            self.handle_speaker_event(
                event.event_type
            )

        except Exception as e:

            print(
                "\n[EVENT SERVICE ERROR]\n"
            )

            print(e)

    def handle_speaker_event(
        self,
        event_type
    ):

        text = None

        # PERSON ENTERED
        if (
            event_type
            == "PERSON_ENTERED"
        ):

            text = (
                "Hello, my name is Alexa."
            )

        # MULTIPLE PEOPLE
        elif (
            event_type
            == "MULTIPLE_PEOPLE"
        ):

            text = (
                "Hi everybody."
            )

        # PERSON LEFT
        elif (
            event_type
            == "PERSON_LEFT"
        ):

            text = (
                "Bye buddy."
            )

        if text is None:
            return

        print(
            f"\n[SPEAKER EVENT] {text}\n"
        )

        try:

            requests.post(
                "http://127.0.0.1:8004/speak",
                json={
                    "text": text
                },
                timeout=3
            )

        except Exception as e:

            print(
                "\n[SPEAKER SERVICE ERROR]\n"
            )

            print(e)