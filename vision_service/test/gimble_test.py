# tools/gimbal_direction_test.py
"""
Decoupled axis-direction test. NO camera, NO PID, NO tracker.

It drives the gimbal to a few known poses so you can SEE which way each axis
moves, then tells you how to map that back to GimbalTracker. Run it, watch the
physical camera, answer the two questions it prints at the end.

Why: in the latest log, PAN centres correctly but TILT does not - on a
perfectly still face (frozen at y=197, above centre) the controller commanded
tilt +10 deg and the face never moved toward centre. That asymmetry is a
direction or servo problem on tilt, not a tuning problem. This isolates it.
"""

import time
import requests

URL = "http://192.168.1.8/move"   # MUST match ESP32Controller(url=...)
TIMEOUT = 1.0
HOLD = 1.8                          # seconds to hold each pose so you can see it


def send(pan, tilt, hold=HOLD):
    try:
        r = requests.get(
            URL,
            params={"s1": int(pan), "s2": int(tilt), "soft": 0, "step": 0, "delay": 0},
            timeout=TIMEOUT,
        )
        print(f"   pan={int(pan):3d} tilt={int(tilt):3d} -> {r.status_code}")
    except Exception as ex:
        print(f"   pan={int(pan):3d} tilt={int(tilt):3d} -> FAILED ({type(ex).__name__}) "
              f"- check IP / WiFi / servo power")
    time.sleep(hold)


print("Centering (pan=90, tilt=110)...")
send(90, 110, hold=2.5)

print("\n[PAN] horizontal sweep - watch the lens:")
print("  pan 90 -> 50"); send(50, 110)
print("  back to 90");   send(90, 110, hold=1.0)
print("  pan 90 -> 130"); send(130, 110)
send(90, 110, hold=2.0)

print("\n[TILT] vertical sweep - watch the lens:")
print("  tilt 110 -> 80"); send(90, 80)
print("  back to 110");    send(90, 110, hold=1.0)
print("  tilt 110 -> 150"); send(90, 150)
send(90, 110, hold=2.0)

print("""
====================  READ THE RESULT  ====================
The tracker currently assumes (both *_dir = -1):
  - HIGHER pan number  -> lens swings the way that pulls a LEFT-of-centre face
                          back toward centre  (CONFIRMED working in your log)
  - HIGHER tilt number -> lens points UP  (so a face above centre drops to centre)

Answer:
  Q1 (sanity): pan 50 vs 130 - did higher numbers swing the lens consistently
               one way? (Pan is already confirmed, this is just a baseline.)
  Q2 (the one that matters): did tilt=150 point the lens UP or DOWN?

  -> If tilt=150 points DOWN (i.e. higher tilt = lens down), the tracker's
     assumption is BACKWARDS. Fix: in GimbalTracker.__init__ set
         self.tilt_dir = +1     # was -1
  -> If tilt=150 correctly points UP but the camera barely moves / is weak /
     jitters, it's a SERVO problem (power brown-out, loose horn, stripped gear),
     not a sign problem. No code change fixes that.
===========================================================
""")