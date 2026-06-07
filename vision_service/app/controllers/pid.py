# app/controllers/pid.py

import time


class PID:
    """
    Frame-driven PID with a robust derivative.

    Two things wreck a visual-servo PID; both are handled here:
      1. Variable frame timing -> dt spikes -> derivative explodes -> servo jitter.
         dt is clamped to a sane window so a slow/fast frame can't blow up D.
      2. Raw derivative amplifies pixel noise. The D term is low-pass filtered.

    Interface is unchanged: PID(kp, ki, kd), .update(error), .reset().
    """

    def __init__(self, kp, ki, kd,
                 dt_min=0.008, dt_max=0.080,
                 d_lpf=0.4, i_clamp=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.dt_min = dt_min      # clamp dt low end -> stops D division blowup
        self.dt_max = dt_max      # clamp dt high end -> stops post-stall D kick
        self.d_lpf = d_lpf        # 0..1, lower = smoother derivative (slightly laggier)
        self.i_clamp = i_clamp    # anti-windup limit on integral; None = off

        self.integral = 0.0
        self.previous_error = 0.0
        self.d_filtered = 0.0
        self.previous_time = time.time()

    def reset(self):
        self.integral = 0.0
        self.previous_error = 0.0
        self.d_filtered = 0.0
        self.previous_time = time.time()

    def update(self, error):
        now = time.time()
        dt = now - self.previous_time
        self.previous_time = now

        # clamp only the dt used for the math; real elapsed still tracked above
        dt = max(self.dt_min, min(self.dt_max, dt))

        # integral (+ optional anti-windup)
        self.integral += error * dt
        if self.i_clamp is not None:
            self.integral = max(-self.i_clamp, min(self.i_clamp, self.integral))

        # raw derivative, then exponential low-pass it
        d_raw = (error - self.previous_error) / dt
        self.d_filtered += self.d_lpf * (d_raw - self.d_filtered)
        self.previous_error = error

        return (self.kp * error
                + self.ki * self.integral
                + self.kd * self.d_filtered)