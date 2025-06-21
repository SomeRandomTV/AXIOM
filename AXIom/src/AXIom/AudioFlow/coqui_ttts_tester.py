import torch
from TTS.api import TTS
#Something
# Get device
device = "cuda" if torch.cuda.is_available() else "cpu"

class CoquiTttsTester:

    def __init__(self, model="tts_models/multilingual/multi-dataset/xtts_v2", speaker="Alison Dietlinde", language="en"):

        """
        Initialize the CoquiTTS Engine

        :param model: str -> the model to use (default is "tts_models/multilingual/multi-dataset/xtts_v2")
        :param speaker: str -> Name of the speaker to use (default is "Alison Dietlinde")
        :param language: str -> The language to use (default is "en" or english)

        :raises ValueError: If the model/speaker/language are not recognized
        """

       # initialize TTS model with whatever model was chosen
        self.tts = TTS(model).to(device)
        self.speakers = self.tts.speakers
        self.models = self.tts.models
        self.model = model
        self.speaker = speaker
        self.language = language
        self.text_to_speak = None

        if model is None:
            raise ValueError("Model Unknown or Not Supported")
        if speaker is None:
            raise ValueError("Speaker Unknown or Not supported")
        if language is None:
            raise ValueError("Language Unknown or Not supported")


    def list_speakers(self) -> None:
        speakers_len = len(self.speakers)

        for speaker in range(speakers_len):
            print(f"Speaker {speaker}: {self.speakers[speaker]}")

    def list_models(self) -> None:
        model_len = len(self.models)
        for model in range(model_len):
            print(f"Model {model}: {self.models[model]}")

    def generate_speech(self, text) -> None:
        self.text_to_speak = text

        self.tts.tts_to_file(
            text=text,
            speaker= self.speaker,
            language="en",
            file_path="output.wav"
        )

    def speak(self):
        """
        Speak the text from audio file
        """




def main():
    tts_engine = CoquiTttsTester()
    tts_engine.list_speakers()
    tts_engine.list_models()
    print(type(tts_engine.generate_speech("hello world")))

if __name__ == "__main__":
    main()



