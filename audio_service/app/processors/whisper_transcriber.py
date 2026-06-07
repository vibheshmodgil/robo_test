import os
import tempfile

import scipy.io.wavfile as wav

from faster_whisper import WhisperModel

from app.config.settings import (
    SAMPLE_RATE,
    WHISPER_MODEL_SIZE
)


class WhisperTranscriber:

    def __init__(self):

        print("[WHISPER] Loading model...")

        self.model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8"
        )

        print("[WHISPER] Model loaded")

    def transcribe_audio(
        self,
        audio_data
    ):

        temp_audio = tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        )

        temp_path = temp_audio.name

        temp_audio.close()

        try:

            wav.write(
                temp_path,
                SAMPLE_RATE,
                audio_data
            )

            segments, info = (
                self.model.transcribe(
                    temp_path,
                    language="en",
                    beam_size=5,
                    vad_filter=True
                )
            )

            full_text = ""

            for segment in segments:

                full_text += segment.text

            return full_text.strip()

        finally:

            if os.path.exists(temp_path):
                os.remove(temp_path)