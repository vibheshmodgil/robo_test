# app/controllers/ema_filter.py

class EMAFilter:
    """
    Adaptive EMA.

    Light smoothing when the face jumps a lot (fast lock-on), heavy smoothing
    when it's nearly still (kills jitter while centred). This is the "best of
    both worlds" alternative to a single fixed alpha that's either too laggy or
    too twitchy.

    Pass a single `alpha` for the old fixed behaviour, or alpha_min/alpha_max
    to enable the adaptive response.
    """

    def __init__(self, alpha=0.35, alpha_min=None, alpha_max=None, jump=50.0):
        self.alpha = alpha
        self.alpha_min = alpha_min if alpha_min is not None else alpha
        self.alpha_max = alpha_max if alpha_max is not None else alpha
        self.jump = jump          # px of movement that maps to full responsiveness
        self.value = None

    def reset(self):
        self.value = None

    def update(self, value):
        if self.value is None:
            self.value = value
            return value

        # big jump in the raw signal -> trust the new reading more
        delta = abs(value - self.value)
        t = min(1.0, delta / self.jump)
        a = self.alpha_min + (self.alpha_max - self.alpha_min) * t

        self.value = a * value + (1 - a) * self.value
        return self.value