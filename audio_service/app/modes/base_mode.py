from abc import ABC, abstractmethod


class BaseMode(ABC):

    @abstractmethod
    def on_enter(self):
        pass

    @abstractmethod
    def on_exit(self):
        pass

    @abstractmethod
    def process_audio(
        self,
        audio_chunk
    ):
        pass