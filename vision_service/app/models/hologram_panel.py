import time

class HologramPanel:
    """One holographic panel. Holds content + appear/disappear animation."""

    def __init__(self, key, anchor="right", offset=(0.0, 0.0),
                 width_frac=0.32, height_frac=0.22, appear=0.30):
        self.key = key
        self.anchor = anchor
        self.offset_x, self.offset_y = offset
        self.width_frac = width_frac
        self.height_frac = height_frac
        self.scale_user = 1.0

        self.title = ""
        self.message = ""
        self.options = []
        self.selected_index = None

        self.appear = appear
        self._anim = 0.0
        self._target = 0.0
        self._last = time.time()

    def show(self, title="", message="", options=None, selected_index=None):
        self.title = title
        self.message = message
        self.options = list(options or [])
        self.selected_index = selected_index
        self._target = 1.0

    def hide(self):
        self._target = 0.0

    def select(self, i):
        if self.options:
            self.selected_index = int(i) % len(self.options)

    def update(self):
        now = time.time()
        dt = now - self._last
        self._last = now
        speed = 1.0 / max(self.appear, 1e-3)
        if self._anim < self._target:
            self._anim = min(self._target, self._anim + dt * speed)
        elif self._anim > self._target:
            self._anim = max(self._target, self._anim - dt * speed)
        return self._anim

    @property
    def alive(self):
        return self._anim > 0.001 or self._target > 0.0

