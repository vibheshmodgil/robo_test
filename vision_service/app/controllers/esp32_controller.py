# app/controllers/esp32_controller.py

import time
import threading
import requests


class ESP32Controller:

    def __init__(self, url="http://192.168.1.8/move",
                 min_interval=0.20, deg_deadband=3.0,
                 soft=0, step=0, delay=0,
                 timeout=1, log=True, stats_interval=2.0):
        # url = your MOTOR ESP32's IP (station mode = 192.168.1.8, its own AP =
        # 192.168.4.1). This is NOT the camera board.
        #
        # min_interval=0.1 -> ~10 Hz. Plenty for face tracking and a fraction of
        # the connection pressure that was causing the connect-timeouts.
        # Smoothing now happens in GimbalTracker (Python) + the non-blocking
        # stepper in the ESP32 loop(), so soft/step/delay here are vestigial.
        self.url = url
        self.min_interval = min_interval
        self.deg_deadband = deg_deadband
        self.soft = soft
        self.step = step
        self.delay = delay
        self.timeout = timeout
        self.log = log
        self.stats_interval = stats_interval

        self._latest = None
        self._last_sent = None
        self._last_time = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()

        # rolling stats: see at a glance whether commands are actually landing
        self._n_ok = 0
        self._n_fail = 0
        self._lat_sum = 0.0
        self._last_stats = time.time()
        self._last_err_time = 0.0

        # keep-alive: reuse one TCP connection instead of a handshake per command
        self._session = requests.Session()

        self._worker_t = threading.Thread(target=self._worker, daemon=True)
        self._worker_t.start()

        # if self.log:
            # print(f"[ESP32] started -> {self.url} "
            #       f"(<= {1 / self.min_interval:.0f} Hz, timeout={self.timeout}s)")

    def move(self, pan, tilt):
        with self._lock:
            self._latest = (int(pan), int(tilt))

    def _print_stats(self, now):
        if not self.log or now - self._last_stats < self.stats_interval:
            return
        total = self._n_ok + self._n_fail
        if total:
            rate = total / (now - self._last_stats)
            avg = (self._lat_sum / self._n_ok) if self._n_ok else 0.0
            # print(f"[ESP32] {rate:.1f} cmd/s | ok={self._n_ok} fail={self._n_fail} "
            #       f"| avg {avg:.0f}ms")
        self._n_ok = self._n_fail = 0
        self._lat_sum = 0.0
        self._last_stats = now

    def _worker(self):
        while not self._stop.is_set():
            time.sleep(0.005)
            now = time.time()
            self._print_stats(now)

            with self._lock:
                cmd = self._latest
            if cmd is None:
                continue

            if now - self._last_time < self.min_interval:
                continue

            # skip sub-degree changes -> no servo buzz when basically centred
            if self._last_sent is not None:
                if (abs(cmd[0] - self._last_sent[0]) < self.deg_deadband and
                        abs(cmd[1] - self._last_sent[1]) < self.deg_deadband):
                    continue

            t0 = time.time()
            try:
                # print(f"[ESP32] sending pan={cmd[0]} tilt={cmd[1]} ...")
                r = self._session.get(
                    self.url,
                    params={"s1": cmd[0], "s2": cmd[1],
                            "soft": self.soft, "step": self.step,
                            "delay": self.delay},
                    timeout=self.timeout
                )
                lat = (time.time() - t0) * 1000.0
                self._n_ok += 1
                self._lat_sum += lat
                self._last_sent = cmd
                self._last_time = now
                # if self.log:
                #     print(f"[ESP32] pan={cmd[0]} tilt={cmd[1]} -> {r.status_code} {lat:.0f}ms")
            except Exception as ex:
                self._n_fail += 1
                self._last_time = now    # respect min_interval before retrying
                # NOTE: don't update _last_sent -> we retry this target next tick
                if self.log and now - self._last_err_time > 1.0:
                    print(f"[ESP32] pan={cmd[0]} tilt={cmd[1]} FAILED: {type(ex).__name__}")
                    self._last_err_time = now

    def stop(self):
        self._stop.set()
        self._session.close()