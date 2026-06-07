from abc import ABC, abstractmethod

class TrackerInterface(ABC):

    @abstractmethod
    def track(self, detections):
        pass