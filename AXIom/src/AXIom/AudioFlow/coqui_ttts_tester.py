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
        # Generate the audio
        wav = self.tts.tts(
            text=text,
            speaker=self.speaker,
            language=self.language
        )

        # Convert to numpy array
        wav = np.array(wav, dtype=np.float32)
        rate = 25000
        # Check if there is audio to play
        if self.stream is None:
            self.stream = self.p.open(
                format     = pyaudio.paFloat32,
                channels   = 1,
                rate       = rate,
                output     = True
            )
        # Play the audio in RAM
        self.stream.write(wav.astype(np.float32).tobytes())


def main():
    tts_engine = CoquiTttsTester()
    tts_engine.generate_and_play("Hello, my name is AURA")
    tts_engine.generate_and_play("I am a robot, I am a robot, I am a robot")

if __name__ == "__main__":
    main()
    print("Done")