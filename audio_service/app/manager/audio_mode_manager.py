import time

from app.audio.audio_states import AudioStates
from app.audio.microphone_manager import microphone_manager

from app.modes.passive_listen_mode import PassiveListenMode
from app.modes.active_listen_mode import ActiveListenMode
from app.modes.workflow_listen_mode import WorkflowListenMode

from app.processors.whisper_transcriber import WhisperTranscriber
from app.detector.wakeword_detector import WakeWordDetector


class AudioModeManager:

    # Ignore the mic briefly after a resume to swallow speaker/output tail.
    RESUME_TAIL_SECONDS = 0.4

    def __init__(self):
        self.current_state = AudioStates.WAITING_WAKEWORD
        self.listening_enabled = True
        self._mic_open_at = 0.0

        whisper_transcriber = WhisperTranscriber()
        wakeword_detector = WakeWordDetector()

        self.handlers = {
            AudioStates.WAITING_WAKEWORD: PassiveListenMode(wakeword_detector),
            AudioStates.LISTENING_COMMAND: ActiveListenMode(whisper_transcriber),
            AudioStates.WORKFLOW_RUNNING: WorkflowListenMode(whisper_transcriber),
        }

    # --- mic gating (used by the pipeline's mic_is_open() check) -------

    def pause_listening(self):
        print("\n[LISTENING PAUSED]\n")
        self.listening_enabled = False
        microphone_manager.clear_queue()

    def resume_listening(self):
        print("\n[LISTENING RESUMED]\n")
        microphone_manager.clear_queue()
        self._mic_open_at = time.time() + self.RESUME_TAIL_SECONDS
        self.listening_enabled = True

    def mic_is_open(self):
        return self.listening_enabled and time.time() >= self._mic_open_at

    # --- state ---------------------------------------------------------

    def set_state(self, state):
        if state == self.current_state:
            return

        print(f"\nSTATE CHANGE: {self.current_state} -> {state}\n")

        microphone_manager.clear_queue()
        self.get_current_handler().on_exit()

        self.current_state = state

        new_handler = self.get_current_handler()
        print(f"ENTERING: {type(new_handler).__name__}")
        new_handler.on_enter()

    def get_current_handler(self):
        return self.handlers[self.current_state]

    def enable_active_mode(self):
        self.set_state(AudioStates.LISTENING_COMMAND)

    def enable_passive_mode(self):
        self.set_state(AudioStates.WAITING_WAKEWORD)

    def enable_workflow_mode(self):
        self.set_state(AudioStates.WORKFLOW_RUNNING)

    def restart_workflow_listening(self):
        # THE FIX: the Java side only ever calls this endpoint
        # (/audio/workflow/fresh), never /audio/workflow. So switch into
        # workflow mode here if we aren't already, THEN re-arm the session.
        # Without the switch, current_state stays LISTENING_COMMAND and every
        # turn is captured by ActiveListenMode -- exactly what the logs show.
        self.set_state(AudioStates.WORKFLOW_RUNNING)            # no-op if already there
        self.handlers[AudioStates.WORKFLOW_RUNNING].reset_session()


audio_mode_manager = AudioModeManager()