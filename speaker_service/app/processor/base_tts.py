from abc import ABC
from abc import abstractmethod


class BaseTTS(ABC):

    @abstractmethod
    def speak(
        self,
        text
    ):
        pass