import threading
import queue

from app.processor.mac_tts import (
    MacTTS
)
from app.processor.window_tts import WindowTTS


class SpeakerPipeline:

    def __init__(self):

        self.tts = (
            WindowTTS()
        )

        self.queue = (
            queue.Queue()
        )

        self.worker_thread = threading.Thread(
            target=self.process_queue,
            daemon=True
        )

        self.worker_thread.start()

    def process_queue(self):

        while True:

            text, completed_event = (
                self.queue.get()
            )

            try:

                print(
                    "\n[SPEAKER START]\n"
                )

                self.tts.speak(text)

                print(
                    "\n[SPEAKER FINISHED]\n"
                )

            finally:

                completed_event.set()

                self.queue.task_done()

    def speak(
        self,
        text
    ):

        completed_event = (
            threading.Event()
        )

        self.queue.put(
            (
                text,
                completed_event
            )
        )

        # WAIT UNTIL SPEECH COMPLETES
        completed_event.wait()