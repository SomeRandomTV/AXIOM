import os
import certifi
import warnings
import speech_recognition as sr
import whisper
#Something
# load SSL file for whisper
os.environ['SSL_CERT_FILE'] = certifi.where()
# suppress warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU*")

"""
Module: MicInput
Handles all microphone transactions (recording/transcribing)
"""
class MicInput:
    def __init__(self):

        """
        Initialize the MicInput class and microphones.
        """
        # recognizer
        self.recognizer = sr.Recognizer()
        # input source
        self.Microphone = sr.Microphone()
        # model to use
        self.model = whisper.load_model("base")
        # transcribed text
        self.model = whisper.load_model("base")
        # transcribed text
        self.text = None

    def set_mic_input(self):
        """
        Transcribe the audio given by the microphone using openai-whisper
        """
        with self.Microphone as source:
            print("Listening...")
            # adjust ambience noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            # record the audio
            audio = self.recognizer.listen(source)
            # write the recorded audio to a file to be transcribed(TODO 'change to transcribe in MEMORY not I/O')
            with open("speech_reference.wav", "wb") as f:
                f.write(audio.get_wav_data())
            try:
                # transcribe with whisper
                result = self.model.transcribe("speech_reference.wav")
                self.text = result["text"]

            except Exception as e:
                print(e)



    def get_text(self):
        return self.text

