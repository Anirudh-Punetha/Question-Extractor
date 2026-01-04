import time

class Timer:
    def __init__(self):
        self.start = time.time()

    def ms(self):
        return int((time.time() - self.start) * 1000)