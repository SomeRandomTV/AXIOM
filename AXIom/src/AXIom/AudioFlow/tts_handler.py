import os
import sys
import io
import tempfile
import subprocess
import logging
import shutil
from gtts import gTTS


"""
Module: TTSHandler
Provides fast, flexible text-to-speech synthesis using gTTS,
supporting both in-memory and file-based streaming with fallback playback.
"""
class TTSHandler:
    def __init__(self, lang: str = 'en', slow: bool = False, log_level: int = logging.INFO):
        """
        Initialize TTSHandler with language and speed settings.

        Args:
            lang (str): Language code (default 'en').
            slow (bool): Use slower speech speed (default False).
            log_level (int): Logging level (default logging.INFO).
        """
        self.lang = lang
        self.slow = slow
        self.logger = self._setup_logger(log_level)
    

    @staticmethod
    def _setup_logger(level: int) -> logging.Logger:
        """
        Set up and return a logger for the TTSHandler.

        Args:
            level (int): Logging level.

        Returns:
            logging.Logger: Configured logger.
        """
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=level
        )
        return logging.getLogger('TTSHandler')

    def synthesize_to_file(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech and save as an MP3 file using gTTS.

        Args:
            text (str): Text to convert.
            output_path (str, optional): Path to save the file. Defaults to system temp.

        Raises:
            ValueError: If text is empty.

        Returns:
            str: Path to the saved MP3 file.
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
        Convert text to speech and return MP3 data as bytes.

        Args:
            text (str): Text to convert.

        Raises:
            ValueError: If text is empty.

        Returns:
            bytes: MP3 audio data in memory.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        self.logger.info("Synthesized TTS audio to memory buffer")
        return buffer.getvalue()

    def play_audio(self, file_path: str) -> None:
        """
        Play an audio file using the system default opener.

        Args:
            file_path (str): Path to the audio file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        opener = 'start' if os.name == 'nt' else ('open' if sys.platform == 'darwin' else 'xdg-open')
        os.system(f"{opener} '{file_path}'")

    def _speak_ffplay(self, text: str, ffplay_path: str) -> None:
        """
        Play streamed audio in memory using ffplay.

        Args:
            text (str): Text to convert and speak.
            ffplay_path (str): Path to ffplay binary.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using ffplay...")
            proc = subprocess.Popen(
                [ffplay_path, '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],
                stdin=subprocess.PIPE
            )
            proc.communicate(audio_bytes)
        except Exception as e:
            self.logger.warning(f"ffplay failed ({e})")
        finally:
            self.logger.info("Done speaking (ffplay).")

    def _speak_afplay(self, text: str, afplay_path: str) -> None:
        """
        Play streamed audio in memory using afplay (macOS).

        Args:
            text (str): Text to convert and speak.
            afplay_path (str): Path to afplay binary.
        """
        audio_bytes = self.synthesize_to_bytes(text)
        try:
            self.logger.info("Trying to speak using afplay...")
            proc = subprocess.Popen([afplay_path, '-'], stdin=subprocess.PIPE)
            proc.communicate(audio_bytes)
        except Exception as e:
            self.logger.warning(f"afplay in-memory failed ({e}), will fallback to file")
        finally:
            self.logger.info("Done speaking (afplay).")

    def _fallback_speak(self, text: str) -> None:
        """
        Fallback to saving audio to a file and using default system playback.

        Args:
            text (str): Text to convert and speak.
        """
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
        Speak text using available playback method in priority order:
        ffplay > afplay > system default player.

        Args:
            text (str): Text to speak.

        Raises:
            ValueError: If text is empty.
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
    tts.speak("Hello, this is AURA, the adaptive real-time assistant. You must keep your responses short, no more than two sentences or 25 words.")


if __name__ == "__main__":
    main()




