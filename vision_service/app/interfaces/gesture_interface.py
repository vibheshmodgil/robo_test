from abc import ABC, abstractmethod

class GestureInterface(ABC):

    @abstractmethod
    def matches(self, landmarks):
        pass

    @abstractmethod
    def name(self):
        pass