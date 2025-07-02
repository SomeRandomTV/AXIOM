import os
import sys
import io
import tempfile
import subprocess
import logging
import shutil
from gtts import gTTS


"""
Module: TTS Handler
Ok, this is very rigged to give us faster in-memory streaming of gtts
If 
"""
class TTSHandler:

    def __init__(self, lang: str = 'en', slow: bool = False, log_level: int = logging.INFO):
        """
        Initialize TTSHandler with language and slow flag.
        Do not pass any arguments to the constructor.
        """
        self.lang = lang
        self.slow = slow
        self.logger = self._setup_logger(log_level)

    # set up the logger
    @staticmethod
    def _setup_logger(level: int) -> logging.Logger:
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",level=level)
        return logging.getLogger('TTSHandler')

    def synthesize_to_file(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech and save as an MP3 file using gtts

        :raises ValueError: If text is empty
        :returnstr: Path to the saved MP3 file
        """

        if not text:
            raise ValueError("Text must not be empty.")
        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), 'tts.mp3')
        tts.save(output_path)
        self.logger.info(f"Saved TTS audio to {output_path}")
        return output_path

    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Convert text to speech and return MP3 data as bytes
        :raises ValueError: If text is empty

        :returns: MP3 data as bytes for speakinging in memory
        """
        if not text:
            raise ValueError("Text must not be empty.")

        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        buffer = io.BytesIO() # create empty buffer
        tts.write_to_fp(buffer) # write to buffer
        self.logger.info("Synthesized TTS audio to memory buffer")
        return buffer.getvalue()

    def play_audio(self, file_path: str) -> None:
        """
        Play an audio file though default system opener
        This is part of the fallback mechanism

        :raises FileNotFoundError: If the file does not exist
        """

        # check if the output file path exists/given
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # create the opener
        opener = 'start' if os.name == 'nt' else ('open' if sys.platform == 'darwin' else 'xdg-open')
        os.system(f"{opener} '{file_path}'")

    def _speak_ffplay(self, text: str, _ffplay: str) -> None:
        """
        Play audio in memory using ffplay
        Very impressive honestly, fuck you
        """
        # create audio bytes
        audio_bytes = self.synthesize_to_bytes(text)

        # trust me guy, hours of doomscrolling subprocess documentation and chatgpt have lead me to this
        try:
            self.logger.info("Trying to speak using ffplay...")
            # create subprocess to stream the audio in memory
            proc = subprocess.Popen([_ffplay, '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],stdin=subprocess.PIPE)
            # send data to subprocess
            proc.communicate(audio_bytes)
        except Exception as e:
            self.logger.warning(f"ffplay failed ({e})")
        finally:
            self.logger.info(f"Done speaking...")

    def _speak_afplay(self, text: str, _afplay: str) -> None:
        # create audio bytes
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using afplay...")
            proc = subprocess.Popen(['afplay', '-'], stdin=subprocess.PIPE)
            proc.communicate(audio_bytes)
            return
        except Exception as e:
            self.logger.warning(f"afplay in-memory failed ({e}), will fallback to file")
        finally:
            self.logger.info(f"Done speaking...")

    def _fallback_speak(self, text: str) -> None:
        path = self.synthesize_to_file(text)
        try:
            self.logger.info("Trying to fallback to file playback...")
            self.play_audio(path)
        except Exception as e:
            self.logger.warning(f"Fallback to file playback failed ({e})")
        finally:
            if os.path.exists(path):
                os.remove(path)
                self.logger.info(f"Removed temporary TTS audio file {path}")

    def speak(self, text: str) -> None:
        """
        Wrapper method to speak some tts text
        First checks for ffplay, if not found, tries afplay, if not found, falls back to file playback

        :raises ValueError: If text is empty
        """

        if not text:
            raise ValueError("Text must not be empty. ARA must say something.")

        print(f"ARA: {text}")
        try:
            ffplay = shutil.which('ffplay')
            afplay = shutil.which('afplay') if sys.platform == "darwin" else None

            if ffplay:
                self._speak_ffplay(text, ffplay)
            elif afplay:
                self._speak_afplay(text, afplay)
            else:
                self._fallback_speak(text)
        except Exception as e:
            self.logger.error(f"Unexpected TTS error: {e}")
            self._fallback_speak(text)
        finally:
            self.logger.info("TTS done.")

def main():

    tts = TTSHandler()
    tts.speak("Hello, this is AURA, the adaptive real time assistant. You must. keep your responses short(1-2 sentences max, no more that 25 words).")

if __name__ == "__main__":
    main()



