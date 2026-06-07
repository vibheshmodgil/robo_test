import time
import numpy as np
from collections import deque

from app.config.settings import (
    VOICE_THRESHOLD,
    WORKFLOW_SILENCE_TIMEOUT,
    MAX_RECORD_TIME,
    WORKFLOW_SUPPRESSION,
    PREROLL_CHUNKS,
)

from app.modes.base_mode import BaseMode
from app.modes.mode_result import ModeResult


class WorkflowListenMode(BaseMode):

    def __init__(self, whisper_transcriber):
        self.whisper_transcriber = whisper_transcriber
        self.audio_buffer = []
        self.preroll = deque(maxlen=PREROLL_CHUNKS)
        self.recording_started = False
        self.last_voice_time = None
        self.record_start_time = None
        self.suppression_until = 0

    def on_enter(self):
        print("\n[MODE] WORKFLOW MODE\n")
        self.reset_session()

    def on_exit(self):
        print("\n[MODE] WORKFLOW EXIT\n")
        self._reset()
        self.suppression_until = 0

    def reset_session(self):
        print("\n[FRESH WORKFLOW SESSION]\n")
        self._reset()
        # Suppress Shiv's own follow-up prompt. Set WORKFLOW_SUPPRESSION
        # ~= the length of that prompt in settings.
        self.suppression_until = time.time() + WORKFLOW_SUPPRESSION

    def _reset(self):
        self.audio_buffer.clear()
        self.preroll.clear()
        self.recording_started = False
        self.last_voice_time = None
        self.record_start_time = None

    def process_audio(self, audio_chunk):

        if time.time() < self.suppression_until:
            return None

        volume = np.abs(audio_chunk).mean()

        if not self.recording_started:
            # Pre-roll only AFTER suppression, so the prompt that was still
            # playing during suppression doesn't leak into the recording.
            self.preroll.append(audio_chunk)

            if volume < VOICE_THRESHOLD:
                return None

            print("\n[WORKFLOW RECORDING STARTED]\n")
            self.recording_started = True
            self.record_start_time = time.time()
            self.last_voice_time = time.time()
            self.audio_buffer.extend(self.preroll)
            return None

        self.audio_buffer.append(audio_chunk)

        if volume > VOICE_THRESHOLD:
            self.last_voice_time = time.time()

        if (
            self.last_voice_time
            and time.time() - self.last_voice_time > WORKFLOW_SILENCE_TIMEOUT
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