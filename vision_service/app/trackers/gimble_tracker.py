# app/trackers/gimble_tracker.py

from app.controllers.pid import PID
from app.controllers.ema_filter import EMAFilter


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


class GimbalTracker:
    """
    Face bbox -> pan/tilt servo angles, CLOSED-LOOP (EMA + PID).

    Per-frame pipeline:
        raw face centre
          -> EMA            adaptive: snappy on a jump, glassy when nearly still
          -> normalise      error mapped to [-1, 1] so gains don't depend on res
          -> soft deadband  kill micro-jitter near centre, no hard snap
          -> PID            filtered derivative + dt-clamped -> no timing jitter
          -> slew cap       max deg/frame -> smooth whip-pans / re-acquire
          -> direction sign -> servo limit clamp

    Tuning knobs, in the order you should reach for them (full notes in the
    message that shipped with this file):
      0. pan_dir / tilt_dir       axis direction (+1 / -1)   <-- verify FIRST
      1. EMA alpha_min/alpha_max  input smoothing (jitter <-> lag)
      2. PID kp                   how hard it chases the target
      3. max_step                 deg/frame slew cap
      4. deadband                 dead zone around centre
      5. PID kd                   damping (overshoot / oscillation)
    """

    def __init__(self):
        # ---- servo state (current commanded angles) -----------------------
        self.pan = 90.0
        self.tilt = 120.0

        # servo travel limits (degrees)
        self.pan_min, self.pan_max = 0.0, 180.0
        self.tilt_min, self.tilt_max = 30.0, 165.0

        # ---- 0. axis direction -------------------------------------------
        # Matched to your WORKING open-loop build: face-left -> pan up,
        # face-above -> tilt up, so both axes use -1 here.
        #
        # The old commented block claimed tilt_dir = +1 "confirmed", but that
        # is the OPPOSITE of the open-loop code you're actually running, so I
        # set tilt_dir = -1 to match the loop that works. If an axis RUNS AWAY
        # to a limit instead of centring, that axis has positive feedback ->
        # flip its sign here.
        self.pan_dir = -1
        self.tilt_dir = -1

        self.lost_frames = 0
        self.prev_face_x = None
        self.prev_face_y = None 

        self.log_counter = 0

        # ---- 2 & 5. PID (normalised error in, deg/frame out) -------------
        # Filtered-derivative PID so kd damps instead of buzzing.
        # ki stays 0: a centring task rarely needs I, and I winds up while the
        # target is lost. If a constant offset never closes, give ki a small
        # value AND set i_clamp (e.g. 0.5) to stop windup.
        self.pan_pid = PID(kp=1, ki=0, kd=0.18, d_lpf=0.3, i_clamp=None)
        self.tilt_pid = PID(kp=1, ki=0, kd=0.18, d_lpf=0.3, i_clamp=None)

        # ---- 1. adaptive EMA on the input (operates in PIXELS) -----------
        self.x_filter = EMAFilter(alpha_min=0.18, alpha_max=0.45, jump=50.0)
        self.y_filter = EMAFilter(alpha_min=0.18, alpha_max=0.45, jump=50.0)

        # ---- 3 & 4. shaping ----------------------------------------------
        self.deadband = 0.04   # normalised (~13 px on a 640-wide frame)
        self.pan_max_step = 1.1
        self.tilt_max_step = 0.7   # deg/frame slew cap -> no jerky re-acquire

        self.debug = False

    def reset(self):
        # Target lost: clear FILTER + PID state only (NOT pan/tilt), so the
        # gimbal holds its last aim. Prevents a derivative kick and an EMA
        # jump from a stale reading when the face re-appears.
        self.x_filter.reset()
        self.y_filter.reset()
        self.pan_pid.reset()
        self.tilt_pid.reset()

        self.prev_face_x = None
        self.prev_face_y = None

        self.lost_frames = 0

    def _soft_deadband(self, e):
        # Continuous deadband: subtract the zone instead of zeroing it, so the
        # output eases in as the target leaves the dead zone (no snap).
        if abs(e) <= self.deadband:
            return 0.0
        return e - self.deadband if e > 0 else e + self.deadband

    def track(self, bbox, width, height):

        if bbox is None:

            # tolerate brief detector misses
            self.lost_frames += 1

            if self.lost_frames < 15:
                return {
                    "pan": self.pan,
                    "tilt": self.tilt
                }

            self.reset()
            return None

        self.lost_frames = 0

        x1, y1, x2, y2 = bbox

        #
        # Face size awareness
        #

        bbox_w = x2 - x1
        face_ratio = bbox_w / width

        if face_ratio > 0.20:
            kp = 1.4
        elif face_ratio > 0.10:
            kp = 1.8
        else:
            kp = 2.2

        self.pan_pid.kp = kp
        self.tilt_pid.kp = kp

        #
        # Face center
        #

        raw_x = (x1 + x2) / 2.0
        raw_y = (y1 + y2) / 2.0

        #
        # EMA
        #

        face_x = self.x_filter.update(raw_x)
        face_y = self.y_filter.update(raw_y)

        #
        # Predictive tracking
        #

        if self.prev_face_x is None:

            self.prev_face_x = face_x
            self.prev_face_y = face_y

        vx = face_x - self.prev_face_x
        vy = face_y - self.prev_face_y

        face_x += vx * 0.35
        face_y += vy * 0.35

        self.prev_face_x = face_x
        self.prev_face_y = face_y

        center_x = width / 2.0
        center_y = height / 2.0

        #
        # Normalized error
        #

        error_x = self._soft_deadband(
            (face_x - center_x) / center_x
        )

        error_y = self._soft_deadband(
            (face_y - center_y) / center_y
        )

        #
        # PID
        #

        pan_output = self.pan_pid.update(error_x)
        tilt_output = self.tilt_pid.update(error_y)
        sat_pan = abs(pan_output) > self.pan_max_step
        sat_tilt = abs(tilt_output) > self.tilt_max_step
        #
        # Slew limit
        #

        d_pan = _clamp(
            pan_output,
            -self.pan_max_step,
            self.pan_max_step
        )

        d_tilt = _clamp(
            tilt_output,
            -self.tilt_max_step,
            self.tilt_max_step
        )

        #
        # Servo update
        #

        self.pan = _clamp(
            self.pan + self.pan_dir * d_pan,
            self.pan_min,
            self.pan_max
        )

        self.tilt = _clamp(
            self.tilt + self.tilt_dir * d_tilt,
            self.tilt_min,
            self.tilt_max
        )

        if self.log_counter % 20 == 0:
            print(
                f"[TRACK] "
                f"face_ratio={face_ratio:.2f} "
                f"kp={kp:.2f} "
                f" sat=({int(sat_pan)},{int(sat_tilt)}) "
                f"pan={self.pan:.1f} "
                f"tilt={self.tilt:.1f} "
                f"err=({error_x:+.3f},{error_y:+.3f}) "
                f"out=({pan_output:+.3f},{tilt_output:+.3f}) "
                f"d=({d_pan:+.3f},{d_tilt:+.3f}) "
                f"lost={self.lost_frames}"
            )
            
        self.log_counter += 1

        return {
            "pan": self.pan,
            "tilt": self.tilt
        }