from abc import ABC, abstractmethod

class CameraInterface(ABC):

    @abstractmethod
    def get_frame(self):
        pass