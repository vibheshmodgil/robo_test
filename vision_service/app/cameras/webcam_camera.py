import time
import threading
import cv2

from app.interfaces.camera_interface import CameraInterface


class WebcamCamera(CameraInterface):
    """
    Threaded camera reader.

    The ESP32-CAM stream lags and stutters; reading it synchronously (the old
    self.cap.read() in get_frame) stalls the whole vision loop -- and your motor
    commands with it -- on every hiccup. This version reads in a background
    thread and always serves the LATEST frame, so get_frame() never blocks.
    It also drops stale frames and auto-reconnects if the stream dies.

    Same interface as before (get_frame / release), so vision_pipeline.py needs
    no changes at all.
    """

    def __init__(self, source=0, name="cam", log=True,
                 reconnect_after=2.0, stats_interval=2.0):
        self.source = source
        self.name = name
        self.log = log
        self.reconnect_after = reconnect_after     # secs of dead reads before reopen
        self.stats_interval = stats_interval

        self.cap = None
        self._frame = None
        self._lock = threading.Lock()
        self._stopped = False

        self._frames = 0
        self._last_ok = time.time()
        self._last_stats = time.time()

        self._open()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _open(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.source)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # fresh frames, not a backlog
        # stop read() blocking forever on a dead stream (FFMPEG backend)
        try:
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 3000)
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 1000)
        except Exception:
            pass
        if self.log:
            ok = self.cap.isOpened()
            print(f"[{self.name}] {'opened' if ok else 'FAILED to open'}: {self.source}")

    def _run(self):
        while not self._stopped:
            ok, f = self.cap.read()
            now = time.time()

            if ok and f is not None:
                with self._lock:
                    self._frame = f
                self._frames += 1
                self._last_ok = now
            else:
                if now - self._last_ok > self.reconnect_after:
                    if self.log:
                        print(f"[{self.name}] stalled {now - self._last_ok:.1f}s, reconnecting...")
                    self._open()
                    self._last_ok = now
                time.sleep(0.02)

            if self.log and now - self._last_stats >= self.stats_interval:
                fps = self._frames / (now - self._last_stats)
                with self._lock:
                    have = self._frame is not None
                print(f"[{self.name}] {fps:.1f} fps {'(frame ok)' if have else '(no frame)'}")
                self._frames = 0
                self._last_stats = now

    def get_frame(self):
        """Latest frame (a copy) or None until the first one arrives."""
        with self._lock:
            return None if self._frame is None else self._frame.copy()

    def release(self):
        self._stopped = True
        if self.cap is not None:
            self.cap.release()