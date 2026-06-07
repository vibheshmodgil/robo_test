import time


class EventManager:

    def __init__(self):

        self.last_event_times = {}

        self.event_history = {}

        self.event_cooldowns = {

            "PERSON_ENTERED": 10,

            "PERSON_LEFT": 10,

            "MULTIPLE_PEOPLE": 20,

            "UNKNOWN_OBJECT": 15
        }

    def should_trigger(
        self,
        event_type
    ):

        current_time = (
            time.time()
        )

        cooldown = (
            self.event_cooldowns
            .get(event_type, 5)
        )

        last_time = (
            self.last_event_times
            .get(event_type, 0)
        )

        if (
            current_time - last_time
            < cooldown
        ):

            return False

        self.last_event_times[
            event_type
        ] = current_time

        return True

    def store_event(
        self,
        event
    ):

        if (
            event.event_type
            not in self.event_history
        ):

            self.event_history[
                event.event_type
            ] = []

        self.event_history[
            event.event_type
        ].append(event)

        print(
            "\n[EVENT STORED]\n"
        )

        print(
            event.event_type
        )

        print(
            event.summary
        )