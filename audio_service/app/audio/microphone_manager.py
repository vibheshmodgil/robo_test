import queue

import numpy as np

import sounddevice as sd

from app.config.settings import (
    SAMPLE_RATE,
    CHANNELS,
    BLOCK_SIZE
)


class MicrophoneManager:

    def __init__(self):

        self.audio_queue = (
            queue.Queue()
        )

        self.device_index = (
            self.find_input_device()
        )

    def find_input_device(self):

        devices = sd.query_devices()

        for index, device in enumerate(devices):

            if (
                "Microphone Array" in device["name"]
                and device["max_input_channels"] > 0
            ):

                print(
                    f"\n[MIC FOUND]"
                    f"\nUsing: {device['name']}\n"
                )

                return index

        for index, device in enumerate(devices):

            if device["max_input_channels"] > 0:

                return index

        raise Exception(
            "No microphone device found"
        )

    def audio_callback(
        self,
        indata,
        frames,
        time,
        status
    ):

        if status:

            print(status)

        audio_chunk = np.copy(indata)

        self.audio_queue.put(audio_chunk)

    def clear_queue(self):

        while (
            not self.audio_queue.empty()
        ):

            self.audio_queue.get()

    def get_queue_size(self):

        return (
            self.audio_queue.qsize()
        )

    def start_stream(self):

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=self.audio_callback,
            blocksize=BLOCK_SIZE,
            device=self.device_index
            # device=1
        )

        self.stream.start()

        print(
            f"\n[MIC STREAM STARTED]"
            f"\nDevice Index: "
            f"{self.device_index}\n"
        )

    def get_audio_chunk(self):

        return (
            self.audio_queue.get()
        )


microphone_manager = (
    MicrophoneManager()
)