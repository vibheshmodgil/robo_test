import cv2
import time

from app.events.event import (
    Event
)

from app.events.event_types import (
    EventTypes
)

from app.events.event_manager import (
    EventManager
)

from app.services.event_service import (
    EventService
)

from app.detectors.person_detectors import (
    PersonDetector) 


class RecordMode:

    def __init__(self):

        self.person_detector = (
            PersonDetector()
        )

        self.event_manager = (
            EventManager()
        )

        self.event_service = (
            EventService()
        )

        self.person_present = False

        self.last_seen_time = 0

        self.missing_frame_count = 0

        self.max_missing_frames = 10

    def process(
        self,
        frame
    ):

        detections = (
            self.person_detector
            .detect(frame)
        )

        current_time = (
            time.time()
        )

        person_detected = (
            len(detections) > 0
        )

        # DRAW BOXES
        for detection in detections:

            x1, y1, x2, y2 = (
                detection["bbox"]
            )

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

        # PERSON ENTERED
        if (
            person_detected
            and not self.person_present
        ):

            self.person_present = True

            event = Event(

                event_type=
                    EventTypes.PERSON_ENTERED,

                summary=
                    "Person entered room"
            )

            self.trigger_event(event)

        # UPDATE LAST SEEN
        if person_detected:

            self.last_seen_time = (
                current_time
            )
            self.missing_frame_count = 0
        else:
            self.missing_frame_count += 1

        # PERSON LEFT
        if (
            self.person_present
            and self.missing_frame_count
            > self.max_missing_frames
        ):

            self.person_present = False

            event = Event(

                event_type=
                    EventTypes.PERSON_LEFT,

                summary=
                    "Person left room"
            )

            self.trigger_event(event)

        # MULTIPLE PEOPLE
        if (
            len(detections) >= 2
        ):

            event = Event(

                event_type=
                    EventTypes.MULTIPLE_PEOPLE,

                summary=
                    "Multiple people detected"
            )

            self.trigger_event(event)

        return frame

    def trigger_event(
        self,
        event
    ):

        should_trigger = (
            self.event_manager
            .should_trigger(
                event.event_type
            )
        )

        if not should_trigger:
            return

        self.event_manager.store_event(
            event
        )

        self.event_service.send_event(
            event
        )