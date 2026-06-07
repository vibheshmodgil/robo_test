from abc import ABC, abstractmethod

class ModeInterface(ABC):

    @abstractmethod
    def process(self, frame):
        pass