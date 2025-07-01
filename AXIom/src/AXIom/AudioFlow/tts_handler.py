import os
import sys
import io
import tempfile
import subprocess
import logging
import shutil
from gtts import gTTS

class TTSHandler:
    """
    Handles text-to-speech synthesis and playback, with optional in-memory streaming (ffplay/afplay) and file fallback.
    """
    def __init__(self, lang: str = 'en', slow: bool = False, log_level: int = logging.INFO):
        self.lang = lang
        self.slow = slow
        self.logger = self._setup_logger(log_level)

    @staticmethod
    def _setup_logger(level: int) -> logging.Logger:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=level
        )
        return logging.getLogger('TTSHandler')

    def synthesize_to_file(self, text: str, output_path: str = None) -> str:
        """
        Convert text to speech and save as an MP3 file.
        """
        if not text:
            raise ValueError("Text must not be empty.")
        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix='.mp3')
            os.close(fd)
        tts.save(output_path)
        self.logger.info(f"Saved TTS audio to {output_path}")
        return output_path

    def synthesize_to_bytes(self, text: str) -> bytes:
        """
        Convert text to speech and return MP3 data as bytes.
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
        Play an audio file via playsound or system default opener.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        opener = 'start' if os.name == 'nt' else ('open' if sys.platform == 'darwin' else 'xdg-open')
        os.system(f"{opener} '{file_path}'")

    def speak(self, text: str, in_memory: bool = True) -> None:
        """
        Very shittly rigged but yessir it works.
        Speaks the text given in memory but can fallback to file playback if ffplay/afplay is not available or doesnt work.
        """
        if not text:
            raise ValueError("Text must not be empty.")

        if in_memory:
            audio_bytes = self.synthesize_to_bytes(text)
            # 1) ffplay streaming
            ffplay = shutil.which('ffplay')
            if ffplay:
                try:
                    proc = subprocess.Popen(
                        [ffplay, '-autoexit', '-nodisp', '-hide_banner', '-loglevel', 'error', '-'],
                        stdin=subprocess.PIPE
                    )
                    proc.communicate(audio_bytes)
                    return
                except Exception as e:
                    self.logger.warning(f"ffplay in-memory failed ({e}), trying afplay...")
            # 2) macOS afplay
            if sys.platform == 'darwin' and shutil.which('afplay'):
                try:
                    proc = subprocess.Popen(['afplay', '-'], stdin=subprocess.PIPE)
                    proc.communicate(audio_bytes)
                    return
                except Exception as e:
                    self.logger.warning(f"afplay in-memory failed ({e}), will fallback to file")

        # in-case shit hits that fan resort to file playback
        path = self.synthesize_to_file(text)
        try:
            self.play_audio(path)
        except Exception as e:
            self.logger.warning(f"ffplay in-memory failed ({e}), trying afplay...")
        finally:
            os.remove(path)
