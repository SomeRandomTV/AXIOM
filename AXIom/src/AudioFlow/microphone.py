# audioflow/MicrophoneTranscribercd
import queue

class MicrophoneTranscriber:
    """
    Handles microphone capture + transcription in one class.
    """

    def __init__(self, model: str = "base"):
        self.model = model
        self.buffer = queue.Queue()
        # TODO: init STT model here (Whisper, Vosk, etc.)

    def start(self):
        """Start listening to microphone."""
        # TODO: start mic stream (PyAudio, sounddevice)
        pass

    def stop(self):
        """Stop listening."""
        pass

    def listen(self) -> str:
        """
        Capture audio and return transcribed text.
        """
        # 1. Get raw audio (from mic or buffer)
        audio_data = self.buffer.get()

        # 2. Run transcription
        # TODO: replace with real STT engine
        return f"[transcribed text from {self.model}]"
