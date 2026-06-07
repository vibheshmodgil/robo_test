# app/controllers/esp32_controller_udp.py
import socket, time, threading


class ESP32ControllerUDP:
    """Fire-and-forget gimbal transport. No TCP handshake -> no ConnectTimeout.
    Same interface as ESP32Controller: .move(pan, tilt) / .stop()."""

    def __init__(self, host="192.168.1.8", port=4210,
                 min_interval=0.05, deg_deadband=2.0, log=True,
                 stats_interval=2.0):
        self.addr = (host, port)
        self.min_interval = min_interval        # 20 Hz, safe over UDP
        self.deg_deadband = deg_deadband
        self.log = log
        self.stats_interval = stats_interval

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._latest = None
        self._last_sent = None
        self._last_time = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._n_ok = 0
        self._n_fail = 0
        self._last_stats = time.time()

        self._t = threading.Thread(target=self._worker, daemon=True)
        self._t.start()

    def move(self, pan, tilt):
        with self._lock:
            self._latest = (int(pan), int(tilt))

    def _worker(self):
        while not self._stop.is_set():
            time.sleep(0.005)
            now = time.time()

            if self.log and now - self._last_stats >= self.stats_interval:
                if self._n_ok + self._n_fail:
                    print(f"[ESP32-UDP] ok={self._n_ok} fail={self._n_fail}")
                self._n_ok = self._n_fail = 0
                self._last_stats = now

            with self._lock:
                cmd = self._latest
            if cmd is None or now - self._last_time < self.min_interval:
                continue
            if self._last_sent is not None:
                if (abs(cmd[0] - self._last_sent[0]) < self.deg_deadband and
                        abs(cmd[1] - self._last_sent[1]) < self.deg_deadband):
                    continue
            try:
                self._sock.sendto(f"{cmd[0]},{cmd[1]}\n".encode(), self.addr)
                self._n_ok += 1
                self._last_sent = cmd
                self._last_time = now
            except Exception as ex:
                self._n_fail += 1
                self._last_time = now
                if self.log:
                    print(f"[ESP32-UDP] {cmd} FAILED: {type(ex).__name__}")

    def stop(self):
        self._stop.set()
        self._sock.close()