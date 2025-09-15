# audioflow/tts_handler.py

VALID_ENGINES = ["gTTS", "CoquiTTS"]

class TTSHandler:
    """
    Converts text into speech audio.
    """
    def __init__(self, engine: str = "gTTS"):
        self.engine = engine

    def speak(self, text: str):
        """
        Synthesize speech from text and play it.
        """
        # TODO: implement with gTTS or pyttsx3
        print(f"[TTS speaking]: {text}")
