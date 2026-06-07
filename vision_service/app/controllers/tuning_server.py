# app/controllers/tuning_server.py
"""
Tuning bridge between the live gimbal pipeline and gimbal_tune_bench.html.

It runs a WebSocket server in a daemon thread (same pattern as the ESP32
controllers) and does two things:

  * STREAMS telemetry  -> every frame's {error, pan, tilt, output, sat, kp, lost}
                          plus the decimated angle actually sent over the wire,
                          at a fixed rate (default 30 Hz), to every connected UI.
  * APPLIES params      <- when the UI moves a slider it sends the full param
                          set; we write each value straight onto the live
                          tracker / PID / EMA / transport / target-tracker
                          objects. Every one of those reads its attributes
                          fresh each frame, so changes take effect immediately
                          with no restart.

On connect the server first sends the rig's CURRENT values to the UI, so the
sliders snap to what the rig is actually running (UI <- rig). After that,
editing a slider pushes UI -> rig. Connecting therefore never clobbers a tune.

------------------------------------------------------------------------------
WIRE PROTOCOL  (matches the bench)
  UI  -> rig : {"type":"params","data":{ ...full param set... }}
  rig -> UI  : {"type":"params","data":{ ... }}          # once, on connect
  rig -> UI  : {"type":"telemetry","t":<sec>, "error_x":.., "error_y":..,
                "pan":.., "tilt":.., "sent_pan":.., "sent_tilt":..,
                "pan_out":.., "tilt_out":.., "sat_pan":0/1, "sat_tilt":0/1,
                "face_ratio":.., "kp":.., "lost":0/1}      # every frame
------------------------------------------------------------------------------

REQUIREMENTS
  pip install websockets

WIRING  (in GimbalMode, where the tracker / transport / target-tracker live)
  from app.controllers.tuning_server import TuningServer
  self.tuning = TuningServer(
      tracker=self.gimbal_tracker,        # the GimbalTracker instance
      transport=self.esp32,               # ESP32Controller / ...UDP (optional)
      target_tracker=self.target_tracker, # TargetTracker (optional)
      host="0.0.0.0", port=8765,
  ).start()
  # ...then in the bench's "Live rig connection" box use  ws://<this-machine-ip>:8765

The tracker must expose `last_telemetry` (the patched GimbalTracker does). The
transport's last-sent pair is read from `_last_sent` if present.

TEST WITHOUT THE RIG
  python -m app.controllers.tuning_server     # serves a synthetic sine tracker
"""

import asyncio
import json
import threading
import time


# ---- UI param key  ->  (object, attribute, cast) ---------------------------
# obj is one of: "tk" tracker, "pp"/"tp" pan/tilt PID, "xf"/"yf" EMA filters,
# "tx" transport, "tt" target tracker.  Handled explicitly below for clarity.

class TuningServer:
    def __init__(self, tracker, transport=None, target_tracker=None,
                 host="0.0.0.0", port=8765, rate=30.0, log=True):
        self.tracker = tracker
        self.transport = transport
        self.target_tracker = target_tracker
        self.host = host
        self.port = port
        self.rate = float(rate)
        self.log = log

        self.clients = set()
        self._thread = None
        self._loop = None
        self._wsmod = None

    # ----------------------------------------------------------------- start
    def start(self):
        if self._thread is not None:
            return self
        self._thread = threading.Thread(target=self._run, name="tuning-ws", daemon=True)
        self._thread.start()
        return self

    def stop(self):
        if self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._loop.stop)
            except Exception:
                pass

    def _run(self):
        try:
            import websockets  # noqa
        except ImportError:
            print("[TUNING] 'websockets' not installed -> `pip install websockets`. "
                  "Tuning server disabled (rig keeps running normally).")
            return
        self._wsmod = websockets
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._main())
        except Exception as ex:
            if self.log:
                print(f"[TUNING] server stopped: {type(ex).__name__}: {ex}")

    async def _main(self):
        wsmod = self._wsmod
        if self.log:
            print(f"[TUNING] websocket up on ws://{self.host}:{self.port}  ({self.rate:.0f} Hz)")
        # ping_interval keeps idle sockets healthy; handler signature tolerates
        # both old (ws, path) and new (ws) websockets versions via *args.
        async with wsmod.serve(self._handler, self.host, self.port, ping_interval=20):
            await self._broadcaster()

    # -------------------------------------------------------------- handler
    async def _handler(self, conn, *args):
        self.clients.add(conn)
        if self.log:
            print(f"[TUNING] client connected ({len(self.clients)} total)")
        try:
            # snap the UI to the rig's current values
            try:
                await conn.send(json.dumps({"type": "params", "data": self._read_params()}))
            except Exception:
                pass
            async for raw in conn:
                try:
                    m = json.loads(raw)
                except Exception:
                    continue
                if m.get("type") == "params" and isinstance(m.get("data"), dict):
                    self._apply_params(m["data"])
        except Exception:
            pass
        finally:
            self.clients.discard(conn)
            if self.log:
                print(f"[TUNING] client gone ({len(self.clients)} total)")

    # ----------------------------------------------------------- broadcaster
    async def _broadcaster(self):
        period = 1.0 / max(1.0, self.rate)
        while True:
            await asyncio.sleep(period)
            if not self.clients:
                continue
            tele = getattr(self.tracker, "last_telemetry", None)
            if not tele:
                continue
            msg = dict(tele)
            msg["type"] = "telemetry"
            msg["t"] = time.time()
            ls = getattr(self.transport, "_last_sent", None) if self.transport else None
            if ls:
                msg["sent_pan"], msg["sent_tilt"] = ls[0], ls[1]
            else:
                msg["sent_pan"] = msg.get("pan")
                msg["sent_tilt"] = msg.get("tilt")
            data = json.dumps(msg)
            for conn in list(self.clients):
                try:
                    await conn.send(data)
                except Exception:
                    self.clients.discard(conn)

    # --------------------------------------------------------- apply params
    def _apply_params(self, d):
        tk, tt, tx = self.tracker, self.target_tracker, self.transport

        def setf(obj, attr, key, cast=float):
            if obj is not None and d.get(key) is not None:
                try:
                    setattr(obj, attr, cast(d[key]))
                except Exception:
                    pass

        # direction & limits
        setf(tk, "pan_dir", "panDir", int)
        setf(tk, "tilt_dir", "tiltDir", int)
        setf(tk, "pan_min", "panMin")
        setf(tk, "pan_max", "panMax")
        setf(tk, "tilt_min", "tiltMin")
        setf(tk, "tilt_max", "tiltMax")

        # EMA (both axes read alpha_min/alpha_max/jump fresh each update)
        for f in (getattr(tk, "x_filter", None), getattr(tk, "y_filter", None)):
            setf(f, "alpha_min", "alphaMin")
            setf(f, "alpha_max", "alphaMax")
            setf(f, "jump", "jump")

        # predictive lead + gain schedule + loss hold  (attrs added by the patch)
        setf(tk, "lead", "lead")
        setf(tk, "kp_close", "kpClose")
        setf(tk, "kp_mid", "kpMid")
        setf(tk, "kp_far", "kpFar")
        setf(tk, "ratio_hi", "ratioHi")
        setf(tk, "ratio_lo", "ratioLo")
        setf(tk, "lost_hold", "lossHold", int)

        # PID (both axes). kp is owned by the gain schedule, so we don't set it.
        for p in (getattr(tk, "pan_pid", None), getattr(tk, "tilt_pid", None)):
            setf(p, "ki", "ki")
            setf(p, "kd", "kd")
            setf(p, "d_lpf", "dLpf")
            setf(p, "dt_min", "dtMin")
            setf(p, "dt_max", "dtMax")
            if p is not None and "iClampOn" in d:
                try:
                    p.i_clamp = float(d.get("iClamp", 0.5)) if d.get("iClampOn") else None
                except Exception:
                    pass

        # slew + deadband
        setf(tk, "deadband", "deadband")
        setf(tk, "pan_max_step", "panMaxStep")
        setf(tk, "tilt_max_step", "tiltMaxStep")

        # transport
        setf(tx, "min_interval", "minInterval")
        setf(tx, "deg_deadband", "degDeadband")

        # target tracker (multi-face)
        setf(tt, "iou_threshold", "iou")
        setf(tt, "max_age", "maxAge")
        setf(tt, "min_hits", "minHits", int)
        setf(tt, "max_shift", "maxShift")

    # ---------------------------------------------------------- read params
    def _read_params(self):
        tk, tt, tx = self.tracker, self.target_tracker, self.transport

        def g(o, a, dv=None):
            return getattr(o, a, dv) if o is not None else dv

        xf = getattr(tk, "x_filter", None)
        pp = getattr(tk, "pan_pid", None)
        ic = g(pp, "i_clamp", None)
        return {
            "panDir": g(tk, "pan_dir", -1), "tiltDir": g(tk, "tilt_dir", -1),
            "panMin": g(tk, "pan_min", 0), "panMax": g(tk, "pan_max", 180),
            "tiltMin": g(tk, "tilt_min", 30), "tiltMax": g(tk, "tilt_max", 165),
            "homePan": g(tk, "home_pan", 90), "homeTilt": g(tk, "home_tilt", 120),
            "alphaMin": g(xf, "alpha_min", 0.18), "alphaMax": g(xf, "alpha_max", 0.45),
            "jump": g(xf, "jump", 50.0),
            "lead": g(tk, "lead", 0.35),
            "kpClose": g(tk, "kp_close", 1.4), "kpMid": g(tk, "kp_mid", 1.8),
            "kpFar": g(tk, "kp_far", 2.2),
            "ratioHi": g(tk, "ratio_hi", 0.20), "ratioLo": g(tk, "ratio_lo", 0.10),
            "ki": g(pp, "ki", 0.0), "kd": g(pp, "kd", 0.18), "dLpf": g(pp, "d_lpf", 0.3),
            "iClampOn": ic is not None, "iClamp": ic if ic is not None else 0.5,
            "dtMin": g(pp, "dt_min", 0.008), "dtMax": g(pp, "dt_max", 0.080),
            "panMaxStep": g(tk, "pan_max_step", 1.1), "tiltMaxStep": g(tk, "tilt_max_step", 0.7),
            "deadband": g(tk, "deadband", 0.04),
            "minInterval": g(tx, "min_interval", 0.05), "degDeadband": g(tx, "deg_deadband", 2.0),
            "lossHold": g(tk, "lost_hold", 15),
            "iou": g(tt, "iou_threshold", 0.30), "maxAge": g(tt, "max_age", 0.8),
            "minHits": g(tt, "min_hits", 3), "maxShift": g(tt, "max_shift", 1.4),
        }


# ============================================================================
# Standalone test: serve a synthetic sine-driven tracker so you can verify the
# bench connects and plots BEFORE wiring the real rig.  ->  python -m app.controllers.tuning_server
# ============================================================================
if __name__ == "__main__":
    import math

    class _Attr:
        def __init__(self, **kw): self.__dict__.update(kw)

    class _FakeTracker:
        def __init__(self):
            self.pan, self.tilt = 90.0, 120.0
            self.pan_min, self.pan_max = 0.0, 180.0
            self.tilt_min, self.tilt_max = 30.0, 165.0
            self.pan_dir, self.tilt_dir = -1, -1
            self.deadband = 0.04
            self.pan_max_step, self.tilt_max_step = 1.1, 0.7
            self.lead = 0.35
            self.kp_close, self.kp_mid, self.kp_far = 1.4, 1.8, 2.2
            self.ratio_hi, self.ratio_lo = 0.20, 0.10
            self.lost_hold = 15
            self.x_filter = _Attr(alpha_min=0.18, alpha_max=0.45, jump=50.0)
            self.y_filter = _Attr(alpha_min=0.18, alpha_max=0.45, jump=50.0)
            self.pan_pid = _Attr(ki=0.0, kd=0.18, d_lpf=0.3, dt_min=0.008, dt_max=0.080, i_clamp=None)
            self.tilt_pid = _Attr(ki=0.0, kd=0.18, d_lpf=0.3, dt_min=0.008, dt_max=0.080, i_clamp=None)
            self.last_telemetry = None

        def spin(self):
            t0 = time.time()
            while True:
                t = time.time() - t0
                ex = 0.45 * math.sin(t * 1.1)
                ey = 0.25 * math.sin(t * 0.7)
                self.pan = 90.0 - ex * 20.0
                self.tilt = 120.0 - ey * 20.0
                self.last_telemetry = {
                    "error_x": round(ex, 4), "error_y": round(ey, 4),
                    "pan": round(self.pan, 2), "tilt": round(self.tilt, 2),
                    "pan_out": round(self.pan_pid.kd + ex, 3), "tilt_out": round(ey, 3),
                    "sat_pan": int(abs(ex) > 0.4), "sat_tilt": 0,
                    "face_ratio": 0.12, "kp": self.kp_mid, "lost": int(abs(ex) > 0.44),
                }
                time.sleep(1.0 / 30.0)

    fake = _FakeTracker()
    threading.Thread(target=fake.spin, daemon=True).start()
    srv = TuningServer(fake, host="0.0.0.0", port=8765)
    srv.start()
    print("[TUNING] demo running. open gimbal_tune_bench.html locally and connect to "
          "ws://127.0.0.1:8765  (Ctrl-C to quit)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[TUNING] bye")     