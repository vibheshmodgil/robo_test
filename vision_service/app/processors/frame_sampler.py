import time

class FrameSampler:

    def __init__(self, fps=5):

        self.interval = 1 / fps

        self.last_time = 0

    def should_process(self):

        current = time.time()

        if current - self.last_time >= self.interval:

            self.last_time = current

            return True

        return False