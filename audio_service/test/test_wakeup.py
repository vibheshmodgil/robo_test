import sounddevice as sd
import numpy as np

from openwakeword.model import Model

SAMPLE_RATE = 16000
BLOCK_SIZE = 1280

print("Loading Jarvis model...")

model = Model(
    wakeword_models=["hey_jarvis"],
    inference_framework="onnx"
)

print("Model loaded!")
print("Say: HEY JARVIS")
print("Press Ctrl+C to stop\n")


def audio_callback(
    indata,
    frames,
    time_info,
    status
):
    if status:
        print(status)

    audio = indata.flatten()

    volume = np.abs(audio).mean()

    audio_int16 = (
        audio * 32767
    ).astype(np.int16)

    prediction = model.predict(audio_int16)

    score = prediction.get(
        "hey_jarvis",
        0.0
    )

    print(
        f"\rVOL={volume:.6f} "
        f"JARVIS_SCORE={score:.4f}",
        end=""
    )

    if score > 0.3:
        print(
            f"\n\nHEY JARVIS DETECTED!"
            f"\nScore={score:.4f}\n"
        )


with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BLOCK_SIZE,
    callback=audio_callback
):
    while True:
        sd.sleep(100)