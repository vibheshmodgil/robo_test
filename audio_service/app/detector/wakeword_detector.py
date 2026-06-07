import numpy as np
import time

from openwakeword.model import Model


class WakeWordDetector:

    def __init__(self):

        print("[WAKEWORD] Loading model...")

        self.model = Model(
            wakeword_models=["hey_jarvis"],
            inference_framework="onnx"
        )

        self.last_detection_time = 0
        self.cooldown_seconds = 5
        self.ignore_until_time = 0

        # Fire on the RAW score (not a 10-frame average), and only after
        # a couple of confident frames in a row. Hysteresis: once it fires
        # it must drop below release_threshold before it can fire again.
        self.trigger_threshold = 0.30
        self.release_threshold = 0.30
        self.required_frames = 1
        self.hot_frames = 0
        self.armed = True

        print("[WAKEWORD] Model loaded")

    def suppress(self, seconds=2.0):
        """Call this the moment TTS starts playing so Shiv doesn't hear
        his own voice and wake himself up."""
        self.ignore_until_time = time.time() + seconds
        try:
            self.model.reset()
        except AttributeError:
            pass

    def detect(self, audio_chunk):

        now = time.time()

        # Don't listen to our own TTS
        if now < self.ignore_until_time:
            return False

        # Refractory period after a real detection
        if now - self.last_detection_time < self.cooldown_seconds:
            return False

        audio_chunk = (audio_chunk.flatten() * 32767).astype(np.int16)

        score = self.model.predict(audio_chunk).get("hey_jarvis", 0.0)
        print(f"\rJARVIS SCORE={score:.4f}", end="")
        # Re-arm only once the wakeword has clearly ended
        if score < self.release_threshold:
            self.armed = True

        # Count consecutive confident frames; any dip resets the count
        if score >= self.trigger_threshold:
            self.hot_frames += 1
        else:
            self.hot_frames = 0

        if self.armed and self.hot_frames >= self.required_frames:
            self.armed = False
            self.hot_frames = 0
            self.last_detection_time = now
            print(f"\nWAKEWORD DETECTED (score={score:.2f})\n")
            return True

        return False