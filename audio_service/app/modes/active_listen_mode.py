import time
import numpy as np
from collections import deque

from app.config.settings import (
    VOICE_THRESHOLD,
    ACTIVE_SILENCE_TIMEOUT,
    MAX_RECORD_TIME,
    ACTIVE_SUPPRESSION,
    PREROLL_CHUNKS,
)

from app.modes.base_mode import BaseMode
from app.modes.mode_result import ModeResult


class ActiveListenMode(BaseMode):

    def __init__(self, whisper_transcriber):
        self.whisper_transcriber = whisper_transcriber
        self.audio_buffer = []
        self.preroll = deque(maxlen=PREROLL_CHUNKS)
        self.recording_started = False
        self.last_voice_time = None
        self.record_start_time = None
        self.suppression_until = 0

    def on_enter(self):
        print("\n[MODE] ACTIVE MODE\n")
        self._reset()
        # Skip the wakeword's own tail at the start of the turn.
        self.suppression_until = time.time() + ACTIVE_SUPPRESSION

    def on_exit(self):
        print("\n[MODE] ACTIVE EXIT\n")
        self._reset()
        self.suppression_until = 0

    def _reset(self):
        self.audio_buffer.clear()
        self.preroll.clear()
        self.recording_started = False
        self.last_voice_time = None
        self.record_start_time = None

    def process_audio(self, audio_chunk):

        volume = np.abs(audio_chunk).mean()

        if not self.recording_started:
            # Keep the pre-roll rolling EVEN during suppression, so a command
            # spoken right after "Alexa" (e.g. "...what is...") isn't lost.
            self.preroll.append(audio_chunk)

        if time.time() < self.suppression_until:
            return None

        if not self.recording_started:

            if volume < VOICE_THRESHOLD:
                return None

            print("\n[ACTIVE RECORDING STARTED]\n")
            self.recording_started = True
            self.record_start_time = time.time()
            self.last_voice_time = time.time()
            # Prepend the lead-in so the first word's soft onset is captured.
            self.audio_buffer.extend(self.preroll)
            return None

        self.audio_buffer.append(audio_chunk)

        if volume > VOICE_THRESHOLD:
            self.last_voice_time = time.time()

        if (
            self.last_voice_time
            and time.time() - self.last_voice_time > ACTIVE_SILENCE_TIMEOUT
        ):
            return self.transcribe()

        if time.time() - self.record_start_time > MAX_RECORD_TIME:
            return self.transcribe()

        return None

    def transcribe(self):

        if len(self.audio_buffer) == 0:
            return None

        audio_data = np.concatenate(self.audio_buffer, axis=0)

        print("\n[WHISPER] Transcribing...\n")

        text = self.whisper_transcriber.transcribe_audio(audio_data)

        self._reset()

        return ModeResult(
            transcription_complete=True,
            wakeword_detected=False,
            text=text
        )