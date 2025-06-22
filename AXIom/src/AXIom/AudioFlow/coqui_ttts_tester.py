import numpy as np
import pyaudio
from TTS.api import TTS

class CoquiTttsTester:
    def __init__(self, model="tts_models/multilingual/multi-dataset/xtts_v2", speaker="Alison Dietlinde", language="en"):
        self.tts     = TTS(model)
        self.speaker = speaker
        self.language= language

        # PyAudio setup
        self.p        = pyaudio.PyAudio()
        self.stream   = None

    def generate_and_play(self, text):
        # Step 1: neural net → numpy array
        wav = self.tts.tts(
            text=text,
            speaker=self.speaker,
            language=self.language
        )
        wav = np.array(wav, dtype=np.float32) # convert to numpy array
        rate = 25000
        # Step 2: open stream (once) at correct sample rate/format
        if self.stream is None:
            self.stream = self.p.open(
                format     = pyaudio.paFloat32,
                channels   = 1,
                rate       = rate,
                output     = True
            )
        # Step 3: write raw bytes
        self.stream.write(wav.astype(np.float32).tobytes())


def main():
    tts_engine = CoquiTttsTester()
    tts_engine.generate_and_play("Hello, my name is AURA")
    tts_engine.generate_and_play("I am a robot, I am a robot, I am a robot")

if __name__ == "__main__":
    main()
    print("Done")