# Live tuning — wiring the bench to the rig

Three files:

| file | where it goes | what it is |
|---|---|---|
| `gimble_tracker.py` | `app/trackers/` (replaces yours) | your tracker + 4 small `# TUNE:` changes |
| `tuning_server.py` | `app/controllers/` (new) | WebSocket bridge: telemetry out, params in |
| `gimbal_tune_bench.html` | anywhere you can open it locally | the tuning UI (now live‑capable) |

---

## 1. Install the one dependency

```bash
pip install websockets
```

## 2. Drop in the patched tracker

`gimble_tracker.py` is your file with **four** literals promoted to attributes (so they can change at runtime) plus a per‑frame telemetry snapshot. The changed lines are marked `# TUNE:`:

- gain schedule `1.4 / 1.8 / 2.2` → `self.kp_close / .kp_mid / .kp_far`
- ratio splits `0.20 / 0.10` → `self.ratio_hi / .ratio_lo`
- predictive lead `* 0.35` → `* self.lead`
- loss hold `< 15` → `< self.lost_hold`
- new: `self.last_telemetry = {…}` written every frame (and during loss)

Behaviour is identical until something moves a slider. If you'd rather not replace the whole file, apply just those five edits to your copy.

## 3. Start the server from GimbalMode

In `gimble_mode.py`, wherever the tracker / transport / target‑tracker already live (probably `__init__`), add:

```python
from app.controllers.tuning_server import TuningServer

self.tuning = TuningServer(
    tracker=self.gimbal_tracker,         # REQUIRED  (rename to your attr)
    transport=self.esp32,                # optional  -> gives sent_pan/sent_tilt
    target_tracker=self.target_tracker,  # optional  -> multi‑face params
    host="0.0.0.0", port=8765,
).start()
```

Only `tracker` is required. It runs in a daemon thread (same as the ESP32 controller) — it does **not** touch your frame loop, and if `websockets` is missing it prints a warning and the rig runs normally.

> Adjust the three attribute names to match your GimbalMode. If you paste `gimble_mode.py` I'll drop these lines in exactly.

## 4. Connect from the bench

1. Open `gimbal_tune_bench.html` **locally** — double‑click the file, or `python -m http.server` next to it. (The in‑chat preview can't reach your LAN, so live connect only works from the local copy.)
2. Find the IP of the machine running the vision service (`ipconfig` / `ip addr`).
3. In the bench → **Export & Connect** → set `ws://<that-ip>:8765` → **Connect**.
   - On a different machine than the rig, make sure port **8765** is open in the firewall.
   - Same machine: `ws://127.0.0.1:8765`.

The chip flips to **LIVE · RIG** and the scopes start drawing real telemetry.

## How the sync behaves

- **On connect:** the rig sends its current values → the sliders snap to what the rig is actually running. Connecting never overwrites a tune.
- **Editing a slider:** pushes that change to the rig instantly (live).
- **Push all ▸:** force‑sends every current slider value to the rig (use after loading a JSON preset, or to apply a sim‑tuned set wholesale).
- **Copy Python:** when you're happy, paste the generated values back into the source so they survive a restart.

## Test without the rig

Verify the UI ↔ server path before touching hardware — this serves a synthetic sine‑driven tracker:

```bash
python -m app.controllers.tuning_server
# then Connect the local bench to ws://127.0.0.1:8765
```

## Wire protocol (if you want to read/extend it)

```
UI  -> rig : {"type":"params","data":{ …full set… }}
rig -> UI  : {"type":"params","data":{ … }}            # once, on connect
rig -> UI  : {"type":"telemetry","t":<sec>,
              "error_x","error_y","pan","tilt",
              "sent_pan","sent_tilt","pan_out","tilt_out",
              "sat_pan","sat_tilt","face_ratio","kp","lost"}   # every frame
```

Params are applied with plain `setattr` onto the live objects, which all read
their attributes fresh each frame — that's why changes take effect with no
restart. `kp` itself is owned by the gain schedule, so the server sets
`kp_close/.kp_mid/.kp_far`, not `pid.kp`.