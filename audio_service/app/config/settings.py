SAMPLE_RATE = 16000

CHANNELS = 1

BLOCK_SIZE = 1280

WHISPER_MODEL_SIZE = "small.en"

VOICE_THRESHOLD = 0.008          # above your ~0.003 background, below ~0.01 speech
ACTIVE_SILENCE_TIMEOUT = 2.0     # end the turn ~1s after they stop
WORKFLOW_SILENCE_TIMEOUT = 2.0   # a touch longer for answers
MAX_RECORD_TIME = 20            # hard cap

# --- anti-clipping / anti-bleed knobs ---
PREROLL_CHUNKS = 6               # ~480 ms of audio kept BEFORE voice is detected,
                                 # so the soft start of the first word survives
ACTIVE_SUPPRESSION = 0.5         # ignore the wakeword's own tail ("...lexa") after it fires
WORKFLOW_SUPPRESSION = 1.2       # set this ~= the length of your follow-up TTS prompt