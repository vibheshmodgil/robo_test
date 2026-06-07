from app.audio.microphone_manager import microphone_manager
from app.manager.audio_mode_manager import audio_mode_manager
from app.services.command_service import CommandService


class AudioPipeline:

    def __init__(self):
        self.microphone_manager = microphone_manager
        self.audio_mode_manager = audio_mode_manager
        self.command_service = CommandService()

    def start(self):
        print("\n[AUDIO PIPELINE] Starting...\n")
        self.microphone_manager.start_stream()

        try:
            while True:
                # Always pull a chunk first. This throttles the loop to the
                # mic's rate and keeps the queue drained — no busy-wait.
                audio_chunk = self.microphone_manager.get_audio_chunk()

                # While the mic is muted (TTS is playing) or inside the
                # short post-resume tail, throw the chunk away instead of
                # feeding it to a mode. THIS is what stops the pipeline from
                # recording the assistant's own spoken lines.
                if not self.audio_mode_manager.mic_is_open():
                    continue

                handler = self.audio_mode_manager.get_current_handler()
                result = handler.process_audio(audio_chunk)

                if result is None:
                    continue

                # WAKEWORD DETECTED
                if result.wakeword_detected:
                    self.microphone_manager.clear_queue()
                    print("\n[AUDIO PIPELINE] Wakeword detected\n")
                    self.command_service.notify_wakeword()
                    continue

                # TRANSCRIPTION COMPLETE
                if result.transcription_complete:
                    self.microphone_manager.clear_queue()
                    print(
                        f"\nUSER SAID ({type(handler).__name__}):\n"
                        f"{result.text}\n"
                    )
                    self.command_service.handle_command(result.text)

        except KeyboardInterrupt:
            print("\n[AUDIO PIPELINE] Stopping...\n")

        except Exception as exception:
            print(f"\n[PIPELINE ERROR]\n{exception}\n")