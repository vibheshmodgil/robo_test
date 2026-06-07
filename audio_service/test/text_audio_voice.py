import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
BLOCK_SIZE = 1280

max_volume = 0.0
volumes = []


def audio_callback(
    indata,
    frames,
    time_info,
    status
):
    global max_volume

    audio = indata.flatten()

    volume = np.abs(audio).mean()

    volumes.append(volume)

    if volume > max_volume:
        max_volume = volume

    avg_volume = np.mean(volumes)

    recommended = max_volume * 0.3

    print(
        f"\rVOL={volume:.6f} "
        f"AVG={avg_volume:.6f} "
        f"MAX={max_volume:.6f} "
        f"REC={recommended:.6f}",
        end=""
    )


print("\n=== MICROPHONE THRESHOLD TEST ===\n")

input("Press ENTER to begin...")

print("\nStay SILENT for 5 seconds...\n")

with sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BLOCK_SIZE,
    callback=audio_callback
):

    sd.sleep(5000)

    noise_floor = (
        np.mean(volumes)
        if volumes
        else 0.0
    )

    print("\n")
    print(
        f"Noise Floor = "
        f"{noise_floor:.6f}"
    )

    volumes.clear()

    print(
        "\nNow SPEAK normally for 10 seconds..."
    )

    sd.sleep(10000)

    speech_average = (
        np.mean(volumes)
        if volumes
        else 0.0
    )

    speech_peak = (
        max(volumes)
        if volumes
        else 0.0
    )

print("\n")

print(
    f"Speech Average = "
    f"{speech_average:.6f}"
)

print(
    f"Speech Peak = "
    f"{speech_peak:.6f}"
)

recommended_threshold = max(
    noise_floor * 4,
    speech_average * 0.35
)

print("\n=== RESULTS ===\n")

print(
    f"Recommended VOICE_THRESHOLD = "
    f"{recommended_threshold:.6f}"
)

print("\nPut this in settings.py:\n")

print(
    f"VOICE_THRESHOLD = "
    f"{recommended_threshold:.6f}"
)